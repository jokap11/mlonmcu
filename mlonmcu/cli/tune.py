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
"""Command line subcommand for the tune stage."""

import copy

import mlonmcu
from mlonmcu.flow import get_available_backend_names
import mlonmcu.flow.tflite
import mlonmcu.flow.tvm
from mlonmcu.models.model import Model
from mlonmcu.session.run import Run
from mlonmcu.session.session import Session
from mlonmcu.cli.common import (
    add_common_options,
    add_context_options,
    add_model_options,
    add_flow_options,
    kickoff_runs,
)
from mlonmcu.config import resolve_required_config

# from mlonmcu.cli.load import handle as handle_load, add_load_options
from mlonmcu.cli.build import add_build_options, handle as handle_build
from mlonmcu.flow import SUPPORTED_BACKENDS, SUPPORTED_FRAMEWORKS
from mlonmcu.session.run import RunStage


def get_parser(subparsers, parent=None):
    """ "Define and return a subparser for the tune subcommand."""
    parser = subparsers.add_parser(
        "tune",
        description="Tune model using the ML on MCU flow.",
        parents=[parent] if parent else [],
        add_help=(parent is None),
    )
    parser.set_defaults(flow_func=handle)
    add_build_options(parser)
    return parser


def handle(args, ctx=None):
    if ctx:
        handle_build(args, context)
    else:
        with mlonmcu.context.MlonMcuContext(path=args.home, lock=True) as context:
            handle_build(args, context)
            kickoff_runs(args, RunStage.TUNE, context)
