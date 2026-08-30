import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "update_version.py"
SPEC = importlib.util.spec_from_file_location("update_version", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
UPDATE_VERSION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPDATE_VERSION)


def create_version_files(root: Path) -> None:
    package_dir = root / "src" / "reflectsonar"
    package_dir.mkdir(parents=True)
    (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (root / "pyproject.toml").write_text('version = "1.0.0"\n', encoding="utf-8")
    (package_dir / "__init__.py").write_text('__version__ = "1.0.0"\n', encoding="utf-8")


def test_update_version_synchronizes_all_declarations(tmp_path):
    create_version_files(tmp_path)

    UPDATE_VERSION.update_version(tmp_path, "2.3.4")

    assert (tmp_path / "VERSION").read_text(encoding="utf-8") == "2.3.4\n"
    assert 'version = "2.3.4"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    package_file = tmp_path / "src" / "reflectsonar" / "__init__.py"
    assert '__version__ = "2.3.4"' in package_file.read_text(encoding="utf-8")


def test_update_version_rejects_non_semantic_version(tmp_path):
    create_version_files(tmp_path)

    with pytest.raises(ValueError, match="MAJOR.MINOR.PATCH"):
        UPDATE_VERSION.update_version(tmp_path, "2.3")
