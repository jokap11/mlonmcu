import os
import argparse
import multiprocessing
import itertools
import logging
from pathlib import Path

# import mlonmcu
import mlonmcu.context
from mlonmcu.session.run import RunStage
from mlonmcu.feature.features import (
    get_available_features,
)
from mlonmcu.config import resolve_required_config
from mlonmcu.logging import get_logger, set_log_level

logger = get_logger()

# MURISCVNN_TOOLCHAIN = "gcc"

FRONTEND = "tflite"

TARGETS = [
    "spike",
    "host_x86",
    "etiss_pulpino",
    "corstone300",
]

AUTOTUNED_TARGETS = ["spike", "etiss_pulpino"]

DEFAULT_TARGETS = [
    "spike",
    # "host_x86",
    # "etiss_pulpino",
    "corstone300",
]

PLATFORM = "mlif"

BACKENDS = [
    "tflmi",
    "tvmaot",
]
DEFAULT_BACKENDS = [
    "tflmi",
    "tvmaot",
]

FEATURES = [
    "muriscvnn",
    "cmsisnn",
]

DEFAULT_FEATURES = [
    "muriscvnn",
    "cmsisnn",
]


def get_target_features(target, enable_default=True, enable_muriscvnn=False, enable_cmsisnn=False):
    TARGET_FEATURES = {
        "spike": [
            *([[]] if enable_default else []),
            *([["muriscvnn"], ["muriscvnn", "vext"], ["muriscvnn", "pext"]] if enable_muriscvnn else []),
            *([["cmsisnn"]] if enable_cmsisnn else []),
        ],
        "host_x86": [
            *([[]] if enable_default else []),
            *([["muriscvnn"]] if enable_muriscvnn else []),
            *([["cmsisnn"]] if enable_cmsisnn else []),
        ],
        "etiss_pulpino": [
            *([[]] if enable_default else []),
            *([["muriscvnn"]] if enable_muriscvnn else []),
            *([["cmsisnn"]] if enable_cmsisnn else []),
        ],
        "corstone300": [
            *([[]] if enable_default else []),
            *([["muriscvnn"]] if enable_muriscvnn else []),
            *([["cmsisnn"]] if enable_cmsisnn else []),
            *([["cmsisnn", "arm_mvei", "arm_dsp"], ["cmsisnn", "arm_dsp"]] if enable_cmsisnn else []),
        ],
    }
    return TARGET_FEATURES[target]


VALIDATE_FEATURES = ["validate", "debug"]

TARGET_ARCH = {
    "spike": "riscv",
    "x86": "x86",
    "etiss_pulpino": "riscv",
    "corstone300": "arm",
}

BACKEND_DEFAULT_FEATURES = {
    "tflmi": [],
    "tvmaot": ["unpacked_api", "usmp"],
}


def get_backend_features(backend, enable_autotuned=False):
    BACKEND_FEATURES = {
        "tflmi": [[]],
        "tvmaot": [[], *([["autotuned"]] if enable_autotuned and target in AUTOTUNED_TARGETS else [])],
    }
    return BACKEND_FEATURES[backend]


def get_backend_config(backend, features, enable_autotuned=False):
    BACKEND_FEATURES = {
        "tflmi": [{}],
        "tvmaot": [
            {},
            *(
                [{"tvmaot.desired_layout": "NCHW"}, {"tvmaot.desired_layout": "NHWC"}]
                if "muricvnnbyoc" not in features and "cmsisnnbyoc" not in features
                else []
            ),
        ],
    }
    return BACKEND_FEATURES[backend]


BACKEND_DEFAULT_CONFIG = {
    "tflmi": {},
    "tvmaot": {"usmp.algorithm": "hill_climb"},
}

VLENS = [64, 128, 256, 512, 1024]

DEFAULT_VLENS = [64, 128, 256, 512, 1024]

STAGE = RunStage.RUN

MODELS = [
    # "sine_model",
    # "magic_wand",
    # "micro_speech",
    # "cifar10",
    # "simple_mnist",
    "aww",
    "vww",
    "resnet",
    "toycar",
]

POSTPROCESSES = [
    # "features2cols",
    "config2cols",
    "filter_cols",
]
POSTPROCESS_CONFIG = {
    "filter_cols.keep": [
        "Model",
        "Backend",
        "Target",
        "Total Cycles",
        "Runtime [s]",
        "Total ROM",
        "Total RAM",
        # "ROM read-only",
        # "ROM code",
        # "ROM misc",
        # "RAM data",
        # "RAM zero-init data",
        "Incomplete",
        "Failing",
        "Features",
        "Comment",
        "config_spike.vlen",
        "Validate",
    ],
    # "filter_cols.drop": [
    #     "Session",
    #     "Run",
    #     "Frontend",
    #     "Framework",
    #     "Platform",
    #     "Num",
    #     "ROM read-only",
    #     "ROM code",
    #     "ROM misc",
    #     "RAM data",
    #     "RAM zero-init data",
    #     "Postprocesses",
    #     "config_tvmaot.unpacked_api",
    #     "config_tvmaot.extra_pass_config",
    #     "config_tvmaot.arena_size",
    #     "config_riscv_gcc.name",
    #     "config_filter_cols.drop",
    #     "config_tvmaot.extra_target",
    #     "config_spike.enable_vext",
    #     "config_spike.arch",
    #     "config_spike.enable_pext",
    #     "config_tflmi.arena_size",
    #     "config_tflmi.ops",
    #     "config_tflm.optimized_kernel",
    #     "config_tvmaot.extra_target_mcpu",
    #     "config_corstone300.enable_mvei",
    #     "config_corstone300.enable_dsp",
    # ],
    "filter_cols.drop_nan": False,
    "filter_cols.drop_const": False,
}


def gen_features(backend, features, validate=False):
    # print("gen_features", backend, features)
    ret = []
    ret.extend(BACKEND_DEFAULT_FEATURES[backend])
    if validate:
        ret += VALIDATE_FEATURES
    if backend == "tvmaot":
        # Rename muriscvnn -> muriscvnnbyoc etc.
        for feature in features:
            if "muriscvnn" in feature:
                ret.append("muriscvnnbyoc")
            elif "cmsisnn" in feature:
                ret.append("cmsisnnbyoc")
            else:
                ret.append(feature)
    else:
        ret += features
    # print("ret", ret)
    return ret


def gen_config(backend, backend_config, features, vlen, enable_postprocesses=False):
    ret = {}
    ret.update(BACKEND_DEFAULT_CONFIG[backend])
    ret.update(backend_config)
    if enable_postprocesses:
        ret.update(POSTPROCESS_CONFIG)
    if "muriscvnn" in features or "muriscvnnbyoc" in features:
        for feature in features:
            if feature == "pext":
                assert vlen == 0
                if backend == "tvmaot":
                    ret["muriscvnnbyoc.mcpu"] = "cortex-m33"
            elif feature == "vext":
                if backend == "tvmaot":
                    ret["muriscvnnbyoc.mcpu"] = "cortex-m55"
                ret["vext.vlen"] = vlen
            # else:
            # assert vlen == 0
    if "cmsisnnbyoc" in features:
        assert backend == "tvmaot"
        if "arm_mvei" in features:
            ret["cmsisnnbyoc.mcpu"] = "cortex-m55"
        elif "arm_dsp" in features:
            ret["cmsisnnbyoc.mcpu"] = "cortex-m33"
    return ret


def benchmark(args):
    with mlonmcu.context.MlonMcuContext() as context:
        session = context.create_session()
        for model in args.models:
            # print("model", model)
            for backend in args.backend:
                # print("backend", backend)
                for target in args.target:
                    # print("target", target)
                    enable_default = not args.skip_default
                    enable_muriscvnn = "muriscvnn" in args.feature
                    enable_cmsisnn = "cmsisnn" in args.feature
                    for target_features in get_target_features(
                        target,
                        enable_default=enable_default,
                        enable_muriscvnn=enable_muriscvnn,
                        enable_cmsisnn=enable_cmsisnn,
                    ):
                        # print("target_features", target_features)
                        enable_autotuned = False
                        if args.autotuned:
                            if (
                                "cmsisnn" not in target_features
                                and "muriscvnn" not in target_features
                                and target == "tvmaot"
                            ):
                                enable_autotuned = True
                        for backend_features in get_backend_features(backend, enable_autotuned=enable_autotuned):
                            # print("backend_features", backend_features)
                            features = list(set(target_features + backend_features))
                            # print("features", features)
                            for backend_config in get_backend_config(
                                backend, features, enable_autotuned=enable_autotuned
                            ):
                                # print("backend_config", backend_config)
                                vlens = [0]
                                if "vext" in features:
                                    vlens = args.vlen
                                # print("vlens", vlens)
                                features = gen_features(backend, features, validate=args.validate)
                                for vlen in vlens:
                                    # print("vlen", vlen)
                                    config = gen_config(
                                        backend, backend_config, features, vlen, enable_postprocesses=args.post
                                    )
                                    # resolve_missing_configs(config, features, target, context)
                                    run = session.create_run(config=config)
                                    run.add_features_by_name(features, context=context)
                                    run.add_platform_by_name(PLATFORM, context=context)
                                    run.add_frontend_by_name(FRONTEND, context=context)
                                    run.add_model_by_name(model, context=context)
                                    run.add_backend_by_name(backend, context=context)
                                    run.add_target_by_name(target, context=context)
                                    if args.post:
                                        run.add_postprocesses_by_name(POSTPROCESSES)
                                    # print("COMMIT")
        # print("sesion.runs", session.runs, len(session.runs))
        session.process_runs(until=STAGE, num_workers=args.parallel, progress=args.progress, context=context)
        report = session.get_reports()
        print(report.df)
        report_file = args.output
        report.export(report_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "models",
        metavar="model",
        type=str,
        # nargs="+",
        nargs="*",
        default=MODELS,
        help="Model to process",
    )
    parser.add_argument(
        "-b",
        "--backend",
        type=str,
        action="append",
        choices=BACKENDS,
        # default=DEFAULT_BACKENDS,
        default=[],
        help=f"Backends to use (default: {DEFAULT_BACKENDS})",
    )
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        action="append",
        choices=TARGETS,
        # default=DEFAULT_TARGETS,
        default=[],
        help=f"Targets to use (default: {DEFAULT_TARGETS}s)",
    )
    parser.add_argument(
        "-f",
        "--feature",
        type=str,
        action="append",
        choices=FEATURES,
        # default=default_features,
        default=[],
        help=f"features to use (default: {DEFAULT_FEATURES})",
    )
    parser.add_argument(
        "--vlen",
        type=int,
        action="append",
        choices=VLENS,
        # default=DEFAULT_VLENS,
        default=[],
        help=f"VLENS to use (RISC-V only) (default: {DEFAULT_VLENS})",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate model outputs (default: %(default)s)",
    )
    parser.add_argument(
        "--autotuned",
        action="store_true",
        help="Use tunung records, if available (default: %(default)s)",
    )
    parser.add_argument(
        "--skip-default",
        dest="skip_default",
        action="store_true",
        help="Do not generate benchmarks for reference runs (default: %(default)s)",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Run postprocesses after the session (default: %(default)s)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Display progress bar (default: %(default)s)",
    )
    parser.add_argument(
        "-p",
        "--progress",
        action="store_true",
        help="Display progress bar (default: %(default)s)",
    )
    parser.add_argument(
        "--parallel",
        metavar="THREADS",
        nargs="?",
        type=int,
        const=multiprocessing.cpu_count(),
        default=1,
        help="Use multiple threads to process runs in parallel (%(const)s if specified, else %(default)s)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        type=str,
        default=os.path.join(os.getcwd(), "out.csv"),
        help="""Output CSV file (default: %(default)s)""",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed messages for easier debugging (default: %(default)s)",
    )
    args = parser.parse_args()
    if not args.backend:
        args.backend = DEFAULT_BACKENDS
    if not args.target:
        args.target = DEFAULT_TARGETS
    if not args.feature:
        args.feature = DEFAULT_FEATURES
    if not args.vlen:
        args.vlen = DEFAULT_VLENS
    if args.verbose:
        set_log_level(logging.DEBUG)
    else:
        set_log_level(logging.INFO)
    benchmark(args)


if __name__ == "__main__":
    main()
