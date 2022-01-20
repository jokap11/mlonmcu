from pathlib import Path
import pytest
import mlonmcu.context


def create_minimal_environment_yaml(path):
    dirname = path.parent.absolute()
    with open(path, "w") as f:
        f.write(f"---\nhome: {dirname}")  # Use defaults

def create_invalid_environment_yaml(path):
    dirname = path.parent.absolute()
    with open(path, "w") as f:
        f.write(f"---\nhome: {dirname}")  # Use defaults

# def test_resolve_environment_file():
# def test_resolve_environment_file_by_name():
# def test_resolve_environment_file_by_file():
# def test_resolve_environment_file_by_dir():
# def test_resolve_environment_file_by_cwd():
# def test_resolve_environment_file_by_env():
# def test_resolve_environment_file_by_default():
# def test_load_recent_sessions():
# def test_create_session():
# def test_load_cache():
# def test_get_session():

def test_open_context(monkeypatch, fake_environment_directory: Path, fake_config_home: Path):
    monkeypatch.chdir(fake_environment_directory)
    create_minimal_environment_yaml(fake_environment_directory / "environment.yml")
    ctx = None
    with mlonmcu.context.MlonMcuContext() as context:
        assert context
        ctx = context
    assert ctx.is_clean

# def test_open_context_by_env(monkeypatch, fake_environment_directory: Path, fake_config_home: Path):
#     monkeypatch.chdir(fake_environment_directory)
#     create_minimal_environment_yaml(fake_environment_directory / "environment.yml")
#     with mlonmcu.context.MlonMcuContext() as context:
#         assert context
#
# def test_open_context_by_default(monkeypatch, fake_environment_directory: Path, fake_config_home: Path):
#     monkeypatch.chdir(fake_environment_directory)
#     create_minimal_environment_yaml(fake_environment_directory / "environment.yml")
#     with mlonmcu.context.MlonMcuContext() as context:
#         assert context
#
# def test_open_context_by_path(monkeypatch, fake_environment_directory: Path, fake_config_home: Path):
#     monkeypatch.chdir(fake_environment_directory)
#     create_minimal_environment_yaml(fake_environment_directory / "environment.yml")
#     with mlonmcu.context.MlonMcuContext() as context:
#         assert context
#
# def test_open_context_by_name(monkeypatch, fake_environment_directory: Path, fake_config_home: Path):
#     monkeypatch.chdir(fake_environment_directory)
#     create_minimal_environment_yaml(fake_environment_directory / "environment.yml")
#     with mlonmcu.context.MlonMcuContext() as context:
#         assert context

def test_reuse_context(monkeypatch, fake_environment_directory: Path, fake_config_home: Path):
    monkeypatch.chdir(fake_environment_directory)
    create_minimal_environment_yaml(fake_environment_directory / "environment.yml")
    with mlonmcu.context.MlonMcuContext() as context:
        assert context
    with mlonmcu.context.MlonMcuContext() as context2:
        assert context2

def test_reuse_context_locked(monkeypatch, fake_environment_directory: Path, fake_config_home: Path):
    monkeypatch.chdir(fake_environment_directory)
    create_minimal_environment_yaml(fake_environment_directory / "environment.yml")
    with mlonmcu.context.MlonMcuContext(lock=True) as context:
        assert context
    with mlonmcu.context.MlonMcuContext(lock=True) as context2:
        assert context2

def test_nest_context(monkeypatch, fake_environment_directory: Path, fake_config_home: Path):
    monkeypatch.chdir(fake_environment_directory)
    create_minimal_environment_yaml(fake_environment_directory / "environment.yml")
    with mlonmcu.context.MlonMcuContext() as context:
        assert context
        with mlonmcu.context.MlonMcuContext() as context2:
            assert context2

def test_nest_context_locked(monkeypatch, fake_environment_directory: Path, fake_config_home: Path):
    monkeypatch.chdir(fake_environment_directory)
    create_minimal_environment_yaml(fake_environment_directory / "environment.yml")
    with mlonmcu.context.MlonMcuContext(lock=True) as context:
        assert context
        with pytest.raises(RuntimeError, match=r".*could\ not\ be\ aquired.*"):
            with mlonmcu.context.MlonMcuContext(lock=True) as context2:
                pass