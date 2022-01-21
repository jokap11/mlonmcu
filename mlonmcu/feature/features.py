"""Definition of MLonMCU features and the feature registry."""

from pathlib import Path
from .feature import (
    BackendFeature,
    FrameworkFeature,
    CompileFeature,
    FrontendFeature,
    TargetFeature,
    SetupFeature,
    FeatureBase,
)


def filter_none(data):
    """Helper function which drop dict items with a None value."""
    assert isinstance(data, dict), "Dict only"
    out = {key: value for key, value in data.items() if value is not None}
    return out


REGISTERED_FEATURES = {}


def register_feature(name):
    """Decorator for adding a feature to the global registry."""

    def real_decorator(obj):
        REGISTERED_FEATURES[name] = obj

    return real_decorator


def get_available_feature_names(feature_type=None):
    """Utility for getting feature names."""
    ret = []
    if feature_type is None:
        return REGISTERED_FEATURES.keys()

    for name, feature in REGISTERED_FEATURES.items():
        if feature_type in list(feature.types()):
            ret.append(name)
    return ret


def get_available_features(feature_type=None, feature_name=None):
    """Utility for looking up features."""
    names = get_available_feature_names(feature_type=feature_type)
    return [
        REGISTERED_FEATURES[name]
        for name in names
        if feature_name is None or name == feature_name
    ]


def get_matching_features(features, feature_type):
    return [feature for feature in features if feature_type in feature.types()]


@register_feature("debug_arena")
class DebugArena(BackendFeature, CompileFeature):
    """Enable verbose printing of arena usage for debugging."""

    def __init__(self, config=None):
        super().__init__("debug_arena", config=config)

    def get_backend_config(self, backend):
        assert backend in [
            "tvmaot",
            "tvmcg",
            "tvmrt",
        ], f"Unsupported feature '{self.name}' for backend '{backend}'"
        # TODO: TFLM also compatible?
        return {f"{backend}.debug_arena": self.enabled}

    # def get_compile_config(self):
    #    return {"mlif.debug_arena": True}

    def get_cmake_args(self):
        val = "ON" if self.enabled else "OFF"
        return [f"-DDEBUG_ARENA={val}"]


@register_feature("muriscvnn")
class Muriscvnn(SetupFeature, FrameworkFeature, CompileFeature):
    """MuriscvNN CMSIS-NN wrappers for TFLite Micro"""

    REQUIRED = ["muriscvnn.lib", "muriscvnn.inc_dir"]

    def __init__(self, config=None):
        super().__init__("muriscvnn", config=config)

    @property
    def muriscvnn_lib(self):
        return str(self.config["muriscvnn.lib"])

    @property
    def muriscvnn_inc_dir(self):
        return str(self.config["muriscvnn.inc_dir"])

    def get_framework_config(self, framework):
        assert (
            framework == "tflite"
        ), f"Unsupported feature '{self.name}' for framework '{framework}'"
        return {f"{framework}.extra_kernel": "muriscvnn"}

    def add_compile_config(self, config):
        # TODO: decide if this is better than directly defining cmake extra args here?
        if "mlif.tflite_micro_libs" in config:
            config["mlif.tflite_micro_libs"].append(self.muriscvnn_lib)
        else:
            config["mlif.tflite_micro_libs"] = [self.muriscvnn_lib]

        if "mlif.tflite_micro_incs" in config:
            config["mlif.tflite_micro_incs"].append(self.muriscvnn_inc_dir)
        else:
            config["mlif.tflite_micro_incs"] = [self.muriscvnn_inc_dir]

        if "mlif.tflite_micro_extra_kernels" in config:
            config["mlif.tflite_micro_extra_kernels"].append("muriscvnn")
        else:
            config["mlif.tflite_micro_extra_kernels"] = ["muriscvnn"]

    def get_required_cache_flags(self):
        return {"tflmc.exe": ["muriscvnn"]}


@register_feature("debug")
class Debug(SetupFeature, CompileFeature):
    """Enable debugging ability of target software."""

    def __init__(self, config=None):
        super().__init__("debug", config=config)

    def get_required_cache_flags(self):
        return {} if self.enabled else {}  # TODO: remove?

    def get_compile_config(self):
        # TODO: or dbg (defined in tasks.py)???
        return {"mlif.debug": self.enabled}


@register_feature("gdbserver")
class GdbServer(TargetFeature):
    """Start debugging session for target software using gdbserver."""

    DEFAULTS = {
        **FeatureBase.DEFAULTS,
        "attach": None,
        "port": None,
    }

    def __init__(self, config=None):
        super().__init__("gdbserver", config=config)

    @property
    def attach(self):
        # TODO: implement get_bool_or_none?
        return bool(self.config["attach"]) if "attach" in self.config else None

    @property
    def port(self):
        return int(self.config["port"]) if "port" in self.config else None

    def get_target_config(self, target):
        assert target in ["host_x86", "etiss_pulpino"]
        return filter_none(
            {
                f"{target}.gdbserver_enable": self.enabled,
                f"{target}.gdbserver_attach": self.attach,
                f"{target}.gdbserver_port": self.port,
            }
        )


@register_feature("etissdbg")
class ETISSDebug(SetupFeature, TargetFeature):
    """Debug ETISS internals."""

    def __init__(self, config=None):
        super().__init__("etissdbg", config=config)

    def get_required_cache_flags(self):
        return (
            {"etiss.install_dir": ["debug"], "etissvp.script": ["debug"]}
            if self.enabled
            else {}
        )

    def get_target_config(self, target):
        assert target in ["etiss_pulpino"]
        return {"etiss_pulpino.debug_etiss": self.enabled}


@register_feature("trace")
class Trace(TargetFeature):
    """Enable tracing of all memory accesses in ETISS."""

    def __init__(self, config=None):
        super().__init__("etissdbg", config=config)

    def get_target_config(self, target):
        assert target in ["etiss_pulpino"]
        return {"etiss_pulpino.trace_memory": self.enabled}


@register_feature("unpacked_api")
class UnpackedApi(BackendFeature):  # TODO: should this be a feature or config only?
    """Use unpacked interface api for TVMAOT backend to reduce stack usage."""

    def __init__(self, config=None):
        super().__init__("unpacked_api", config=config)

    def get_backend_config(self, backend):
        assert backend in [
            "tvmaot"
        ], f"Unsupported feature '{self.name}' for backend '{backend}'"
        return {f"{backend}.unpacked_api": self.enabled}


@register_feature("packed")
class Packed(
    FrameworkFeature, FrontendFeature, BackendFeature, SetupFeature, CompileFeature
):
    """Sub-8-bit and sparsity feature for TFLite Micro kernels."""

    def __init__(self, config=None):
        super().__init__("packed", config=config)

    def get_framework_config(self, framework):
        raise NotImplementedError

    def get_frontend_config(self, frontend):
        assert frontend in [
            "tflite"
        ], f"Unsupported feature '{self.name} for frontend '{frontend}''"
        return {f"{frontend}.use_packed_weights": self.enabled}

    def get_backend_config(self, backend):
        raise NotImplementedError

    def get_required_cache_flags(self):
        return {"tflmc.exe": ["packed"]}

    def get_cmake_args(self):
        val = "ON" if self.enabled else "OFF"
        return [f"-DDEBUG_ARENA={val}"]


@register_feature("packing")
class Packing(FrontendFeature):
    """Sub-8-bit and sparse weight packing for TFLite Frontend."""

    def __init__(self, config=None):
        super().__init__("packing", config=config)

    def get_frontend_config(self, frontend):
        assert frontend in [
            "tflite"
        ], f"Unsupported feature '{self.name} for frontend '{frontend}''"
        raise NotImplementedError
        return {f"{frontend}.pack_weights": self.enabled}


@register_feature("fallback")
class Fallback(FrameworkFeature, CompileFeature):
    """(Unimplemented) TFLite Fallback for unsupported and custom operators in TVM."""

    DEFAULTS = {
        **FeatureBase.DEFAULTS,
        "config_file": None,
    }

    def __init__(self, config=None):
        super().__init__("fallback", config=config)

    @property
    def config_file(self):
        return str(self.config["config_file"]) if "config_file" in self.config else None

    def get_framework_config(self, framework):
        assert framework in [
            "tvm"
        ], f"Usupported fetaure '{self.name}' for framework '{framework}'"
        raise NotImplementedError
        return filter_none(
            {
                f"{framework}.fallback_enable": self.enabled,
                f"{framework}.fallback_config_file": self.config_file,
            }
        )

    # -> hard to model..., preprocess for tflmc?


@register_feature("memplan")
class Memplan(FrameworkFeature):
    """Custom TVM memory planning feature by (@rafzi)"""

    def __init__(self, config=None):
        super().__init__("memplan", config=config)

    def get_framework_config(self, framework):
        assert framework in [
            "tvm"
        ], f"Usupported fetaure '{self.name}' for framework '{framework}'"
        return {"tvm.memplan_enable": self.enabled}

    # -> enable this via backend


@register_feature("fusetile")
class Fusetile(FrameworkFeature):
    """WIP TVM feature by (@rafzi)"""

    def __init__(self, config=None):
        super().__init__("fusetile", config=config)

    def get_framework_config(self, framework):
        assert framework in [
            "tvm"
        ], f"Usupported fetaure '{self.name}' for framework '{framework}'"
        return {"tvm.fusetile_enable": self.enabled}

    # -> enable this via backend


@register_feature("visualize")
class Visualize(BackendFeature):
    """Visualize TVM relay models."""

    # Bokeh backend has additional python requirements: graphviz, pydot, bokeh >= 2.3.1
    # TODO: add tflite visualizer? (Frontend)

    DEFAULTS = {
        **FeatureBase.DEFAULTS,
        "mode": "cli",  # Alternative: bokeh
    }

    def __init__(self, config=None):
        super().__init__("visualize", config=config)

    @property
    def mode(self):
        value = self.config["mode"] if "mode" in self.config else None
        if value:
            assert value.lower() in ["cli", "bokeh"]
        return value

    def get_backend_config(self, backend):
        assert (
            backend in TVM_BACKENDS  # TODO: undefined!
        ), f"Unsupported feature '{self.name}' for backend '{backend}'"
        return NotImplementedError
        return filter_none(
            {
                f"{backend}.visualize_enable": self.enabled,
                f"{backend}.visualize_mode": self.mode,
            }
        )


@register_feature("autotuned")
class Autotuned(BackendFeature):
    """Use existing TVM autotuning logs in backend."""

    # TODO: FronendFeature to collect tuning logs or will we store them somewhere else?

    DEFAULTS = {
        **FeatureBase.DEFAULTS,
        "results_file": None,
    }

    def __init__(self, config=None):
        super().__init__("autotuned", config=config)

    def results_file(self):
        return (
            str(self.config["results_file"]) if "results_file" in self.config else None
        )

    def get_backend_config(self, backend):
        assert backend in ["tvmaot", "tvmcg", "tvmrt"]  # TODO: backend in TVM_BACKENDS
        # TODO: error handling her eor on backend?
        return filter_none(
            {
                f"{backend}.autotuning_tuned": self.enabled,
                f"{backend}.autotuning_results_file": self.results_file,
            }
        )


@register_feature("autotune")
class Autotune(BackendFeature):
    """Use the TVM autotuner inside the backend to generate tuning logs."""

    DEFAULTS = {
        **FeatureBase.DEFAULTS,
        "results_file": None,
        "append": None,
        "tuner": None,
        "trial": None,
        "early_stopping": None,
        "num_workers": None,
        "max_parallel": None,
    }

    def __init__(self, config=None):
        super().__init__("autotune", config=config)

    @property
    def results_file(self):
        return (
            str(self.config["results_file"]) if "results_file" in self.config else None
        )

    @property
    def append(self):
        return bool(self.config["append"]) if "append" in self.config else None

    @property
    def tuner(self):
        return bool(self.config["tuner"]) if "tuner" in self.config else None

    @property
    def trials(self):
        return int(self.config["trials"]) if "trials" in self.config else None

    @property
    def early_stopping(self):
        return (
            int(self.config["early_stopping"])
            if "early_stopping" in self.config
            else None
        )

    @property
    def num_workers(self):
        return int(self.config["num_workers"]) if "num_workers" in self.config else None

    @property
    def max_parallel(self):
        return (
            int(self.config["max_parallel"]) if "max_parallel" in self.config else None
        )

    def get_backend_config(self, backend):
        assert backend in ["tvmaot", "tvmcg", "tvmrt"]  # TODO: backend in TVM_BACKENDS
        # TODO: figure out a default path automatically
        return filter_none(
            {
                f"{backend}.autotuning_enable": self.enabled,
                f"{backend}.autotuning_results_file": self.results_file,
                f"{backend}.autotuning_append": self.append,
                f"{backend}.autotuning_tuner": self.tuner,
                f"{backend}.autotuning_trials": self.trials,
                f"{backend}.autotuning_early_stopping": self.early_stopping,
                f"{backend}.autotuning_num_workers": self.num_workers,
                f"{backend}.autotuning_max_parallel": self.max_parallel,
            }
        )


# Frontend features
TFLITE_FRONTEND_FEATURES = ["packing"]
FRONTEND_FEATURES = TFLITE_FRONTEND_FEATURES

# Framework features
TFLITE_FRAMEWORK_FEATURES = ["packing", "muriscvnn"]
TVM_FRAMEWORK_FEATURES = ["autotuning"]
FRAMEWORK_FEATURES = TFLITE_FRAMEWORK_FEATURES + TVM_FRAMEWORK_FEATURES

# Backend features
TFLITE_BACKEND_FEATURES = []
TVMAOT_BACKEND_FEATURES = ["unpacked_api"]
TVM_BACKEND_FEATURES = TVMAOT_BACKEND_FEATURES
BACKEND_FEATURES = TFLITE_BACKEND_FEATURES + TVM_BACKEND_FEATURES

# Traget features
TARGET_FEATURES = ["trace"]

ALL_FEATURES = (
    FRONTEND_FEATURES + FRAMEWORK_FEATURES + BACKEND_FEATURES + TARGET_FEATURES
)