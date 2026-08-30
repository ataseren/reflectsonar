#!/usr/bin/env python3
"""Keep ReflectSonar's release version declarations synchronized."""

import argparse
import re
from pathlib import Path
from typing import Dict

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def update_version(root: Path, version: str) -> Dict[Path, str]:
    """Update every authoritative version file and return its new content."""
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("Version must use MAJOR.MINOR.PATCH format")

    replacements = {
        root / "VERSION": (None, f"{version}\n"),
        root
        / "pyproject.toml": (
            re.compile(r'(?m)^version = "[^"]+"$'),
            f'version = "{version}"',
        ),
        root
        / "src"
        / "reflectsonar"
        / "__init__.py": (
            re.compile(r'(?m)^__version__ = "[^"]+"$'),
            f'__version__ = "{version}"',
        ),
    }

    updated = {}
    for path, (pattern, replacement) in replacements.items():
        if pattern is None:
            content = replacement
        else:
            original = path.read_text(encoding="utf-8")
            content, count = pattern.subn(replacement, original)
            if count != 1:
                raise ValueError(f"Expected one version declaration in {path}, found {count}")
        path.write_text(content, encoding="utf-8")
        updated[path] = content

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Release version in MAJOR.MINOR.PATCH format")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    update_version(project_root, args.version)
    print(f"Updated ReflectSonar version to {args.version}")


if __name__ == "__main__":
    main()
