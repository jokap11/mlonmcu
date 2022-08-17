#
# Copyright (c) 2022 TUM Department of Electrical and Computer Engineering.
#
# This file is part of MLonMCU.
# See https://github.com/tum-ei-eda/mlonmcu.git for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""MLonMCU Spike Target definitions"""

import os
import re
from pathlib import Path

from mlonmcu.logging import get_logger
from mlonmcu.config import str2bool
from mlonmcu.feature.features import SUPPORTED_TVM_BACKENDS
from mlonmcu.target.common import cli, execute
from mlonmcu.target.metrics import Metrics
from .riscv import RISCVTarget

logger = get_logger()


class SpikeTarget(RISCVTarget):
    """Target using the riscv-isa-sim (Spike) RISC-V simulator."""

    FEATURES = RISCVTarget.FEATURES + ["vext", "pext", "cachesim", "log_instrs"]

    DEFAULTS = {
        **RISCVTarget.DEFAULTS,
        "enable_vext": False,
        "enable_pext": False,
        "vlen": 0,  # vectorization=off
        "elen": 32,
        "spikepk_extra_args": [],
        "end_to_end_cycles": False,
    }
    REQUIRED = RISCVTarget.REQUIRED + ["spike.exe", "spike.pk"]

    def __init__(self, name="spike", features=None, config=None):
        super().__init__(name, features=features, config=config)

    @property
    def spike_exe(self):
        return Path(self.config["spike.exe"])

    @property
    def spike_pk(self):
        return Path(self.config["spike.pk"])

    @property
    def enable_vext(self):
        value = self.config["enable_vext"]
        return str2bool(value) if not isinstance(value, (bool, int)) else value

    @property
    def enable_pext(self):
        value = self.config["enable_pext"]
        return str2bool(value) if not isinstance(value, (bool, int)) else value

    @property
    def extensions(self):
        ret = super().extensions
        if self.enable_pext and "p" not in ret:
            ret.append("p")
        if self.enable_vext and ("v" not in ret and "zve32x" not in ret and "zve32f" not in ret):
            if self.elen == 32:  # Required to tell the compiler that EEW is not allowed...
                # if self.enable_fpu:
                if True:
                    ret.append("zve32x")
                else:
                    ret.append("zve32f")
            else:
                ret.append("v")
        return ret

    @property
    def attr(self):
        attrs = super().attr.split(",")
        if self.enable_vext and f"+zvl{self.vlen}b" not in attrs:
            attrs.append(f"+zvl{self.vlen}b")
        return ",".join(attrs)

    @property
    def vlen(self):
        return int(self.config["vlen"])

    @property
    def elen(self):
        return int(self.config["elen"])

    @property
    def spikepk_extra_args(self):
        return self.config["spikepk_extra_args"]

    @property
    def end_to_end_cycles(self):
        value = self.config["end_to_end_cycles"]
        return str2bool(value) if not isinstance(value, (bool, int)) else value

    def exec(self, program, *args, cwd=os.getcwd(), **kwargs):
        """Use target to execute a executable with given arguments"""
        spike_args = []
        spikepk_args = []

        arch_after = self.arch.replace("zve32x", "v").replace("zve32f", "v")
        spike_args.append(f"--isa={arch_after}")

        if len(self.extra_args) > 0:
            spike_args.extend(self.extra_args)

        if self.end_to_end_cycles:
            spikepk_args.append("-s")

        if len(self.spikepk_extra_args) > 0:
            spikepk_args.extend(self.spikepk_extra_args.split(" "))

        if self.enable_vext:
            assert self.vlen > 0
            spike_args.append(f"--varch=vlen:{self.vlen},elen:{self.elen}")
        else:
            assert self.vlen == 0

        if self.timeout_sec > 0:
            raise NotImplementedError

        ret = execute(
            self.spike_exe.resolve(),
            *spike_args,
            self.spike_pk.resolve(),
            *spikepk_args,
            program,
            *args,
            **kwargs,
        )
        return ret

    def parse_stdout(self, out):
        if self.end_to_end_cycles:
            cpu_cycles = re.search(r"(\d*) cycles", out)
        else:
            cpu_cycles = re.search(r"Total Cycles: (.*)", out)
        if not cpu_cycles:
            logger.warning("unexpected script output (cycles)")
            cycles = None
        else:
            cycles = int(float(cpu_cycles.group(1)))
        # mips = None  # TODO: parse mips?
        return cycles

    def get_metrics(self, elf, directory, handle_exit=None):
        out = ""
        if self.print_outputs:
            out += self.exec(elf, cwd=directory, live=True, handle_exit=handle_exit)
        else:
            out += self.exec(
                elf, cwd=directory, live=False, print_func=lambda *args, **kwargs: None, handle_exit=handle_exit
            )
        cycles = self.parse_stdout(out)

        metrics = Metrics()
        metrics.add("Cycles", cycles)

        return metrics, out, []

    def get_platform_defs(self, platform):
        ret = super().get_platform_defs(platform)
        if self.enable_pext:
            ret["RISCV_RVP_MAJOR"] = "0"
            ret["RISCV_RVP_MINOR"] = "96"
        if self.enable_vext:
            ret["RISCV_RVV_MAJOR"] = "1"
            ret["RISCV_RVV_MINOR"] = "0"
            ret["RISCV_RVV_VLEN"] = self.vlen
        return ret

    def get_backend_config(self, backend):
        ret = super().get_backend_config(backend)
        if backend in SUPPORTED_TVM_BACKENDS:
            ret.update({"target_model": "spike-rv32"})
            if self.enable_pext or self.enable_vext:
                ret.update(
                    {
                        # Warning: passing kernel layouts does not work with upstream TVM
                        # TODO: allow passing map?
                        "desired_layout": "NHWC:HWOI",
                    }
                )
        return ret


if __name__ == "__main__":
    cli(target=SpikeTarget)