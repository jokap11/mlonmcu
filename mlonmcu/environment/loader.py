import os
import yaml
import pathlib
import logging

from .config import *

# def load_environment_from_file(filename):
#     """Utility to initialize a mlonmcu environment from a YAML file."""
#     if isinstance(filename, str):
#         filename = pathlib.Path(filename)
#     with open(filename, encoding="utf-8") as yaml_file:
#         data = yaml.safe_load(yaml_file)
#         if data:
#             if "home" in data:
#                 print(data["home"], filename.parent)
#                 assert os.path.realpath(data["home"]) == os.path.realpath(filename.parent)
#             else:
#                 data["home"] = filename.parent
#             env = Environment(data)
#             return env
#         raise RuntimeError(f"Error opening environment file: {filename}")
#     return None


def load_environment_from_file(filename, base):
    """Utility to initialize a mlonmcu environment from a YAML file."""
    if isinstance(filename, str):
        filename = pathlib.Path(filename)
    with open(filename, encoding="utf-8") as yaml_file:
        loaded = yaml.safe_load(yaml_file)
        if not loaded:
            raise RuntimeError("Invalid YAML contents")
        if "home" in loaded:
            home = loaded["home"]
        else:
            home = None
        if "logging" in loaded:
            if "level" in loaded["logging"]:
                log_level = logging.getLevelName(loaded["logging"]["level"])
            else:
                log_level = None
            if "to_file" in loaded["logging"]:
                log_to_file = bool(loaded["logging"]["to_file"])
            else:
                log_to_file = None
            if "rotate" in loaded["logging"]:
                log_rotate = bool(loaded["logging"]["rotate"])
            else:
                log_rotate = None
        else:
            log_level = None
            log_to_file = False
            log_rotate = False
        if "paths" in loaded:
            paths = {}
            for key in loaded["paths"]:
                path = loaded["paths"][key]
                if isinstance(path, list):
                    paths[key] = []
                    for p in path:
                        paths[key].append(PathConfig(p, base=home))
                else:
                    paths[key] = PathConfig(path, base=home)
        else:
            paths = None
        if "repos" in loaded:
            repos = {}
            for key in loaded["repos"]:
                repo = loaded["repos"][key]
                if "url" not in repo:
                    raise RuntimeError("Missing field 'url' in YAML file")
                if "ref" in repo:
                    repos[key] = RepoConfig(repo["url"], ref=repo["ref"])
                else:
                    repos[key] = RepoConfig(repo["url"])
        else:
            repos = None
        default_framework = None
        default_backends = {}
        if "frameworks" in loaded:
            frameworks = []
            default_framework = loaded["frameworks"].pop("default", None)
            for key in loaded["frameworks"]:
                framework = loaded["frameworks"][key]
                if "enabled" in framework:
                    enabled = bool(framework["enabled"])
                else:
                    enabled = False
                backends = []
                if "backends" in framework:
                    default_backend = framework["backends"].pop("default", None)
                    default_backends[key] = default_backend
                    for key2 in framework["backends"]:
                        backend = framework["backends"][key2]
                        if "enabled" in backend:
                            enabled2 = bool(backend["enabled"])
                        else:
                            enabled2 = True
                        backend_features = []
                        if "features" in backend:
                            for key3 in backend["features"]:
                                supported = bool(backend["features"][key3])
                                backend_features.append(BackendFeatureConfig(key3, backend=key2, supported=supported))
                        backends.append(BackendConfig(key2, enabled=enabled2, features=backend_features))
                framework_features = []
                if "features" in framework:
                    for key2 in framework["features"]:
                        supported = bool(framework["features"][key2])
                        framework_features.append(FrameworkFeatureConfig(key2, framework=key, supported=supported))
                frameworks.append(
                    FrameworkConfig(
                        key,
                        enabled=enabled,
                        backends=backends,
                        features=framework_features,
                    )
                )
        else:
            frameworks = None
        if "frontends" in loaded:
            frontends = []
            for key in loaded["frontends"]:
                frontend = loaded["frontends"][key]

                if "enabled" in frontend:
                    enabled = frontend["enabled"]
                else:
                    enabled = True
                frontend_features = []
                if "features" in frontend:
                    for key2 in frontend["features"]:
                        supported = bool(frontend["features"][key2])
                        frontend_features.append(FrontendFeatureConfig(key2, frontend=key, supported=supported))
                frontends.append(FrontendConfig(key, enabled=enabled, features=frontend_features))
        else:
            frontends = None
        default_target = None
        if "targets" in loaded:
            targets = []
            default_target = loaded["targets"].pop("default", None)
            for key in loaded["targets"]:
                target = loaded["targets"][key]
                if "enabled" in target:
                    enabled = target["enabled"]
                else:
                    enabled = True
                target_features = []
                if "features" in target:
                    for key2 in target["features"]:
                        supported = bool(target["features"][key2])
                        target_features.append(TargetFeatureConfig(key2, target=key, supported=supported))
                targets.append(TargetConfig(key, enabled=enabled, features=target_features))
        else:
            targets = None
        if "vars" in loaded:
            variables = loaded["vars"]
        else:
            variables = None
        defaults = DefaultsConfig(
            log_level=log_level,
            log_to_file=log_to_file,
            log_rotate=log_rotate,
            default_framework=default_framework,
            default_backends=default_backends,
            default_target=default_target,
        )
        env = base(
            home,
            defaults=defaults,
            paths=paths,
            repos=repos,
            frameworks=frameworks,
            frontends=frontends,
            targets=targets,
            variables=variables,
        )
        return env
        # print("env", env)