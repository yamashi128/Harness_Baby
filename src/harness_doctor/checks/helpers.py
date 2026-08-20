"""Small, bounded helpers used by checks."""

from __future__ import annotations

import configparser
import tomllib
from pathlib import Path
from typing import Any

MAX_TEXT_BYTES = 1_000_000


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def load_toml(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.is_file():
        return {}, None
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream), None
    except (OSError, tomllib.TOMLDecodeError) as error:
        return {}, type(error).__name__


def config_has_section(path: Path, prefix: str) -> bool:
    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except (OSError, configparser.Error):
        return False
    return any(
        section == prefix or section.startswith(f"{prefix}:") for section in parser.sections()
    )


def nested_mapping(data: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def project_dependency_names(pyproject: dict[str, Any]) -> set[str]:
    entries: list[str] = []
    project = pyproject.get("project")
    if isinstance(project, dict):
        dependencies = project.get("dependencies", [])
        if isinstance(dependencies, list):
            entries.extend(str(item) for item in dependencies)
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for group in optional.values():
                if isinstance(group, list):
                    entries.extend(str(item) for item in group)

    poetry = nested_mapping(pyproject, "tool", "poetry", "dependencies")
    entries.extend(str(item) for item in poetry)
    return {_dependency_name(entry) for entry in entries}


def requirement_names(path: Path) -> set[str]:
    names: set[str] = set()
    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        names.add(_dependency_name(line))
    return names


def _dependency_name(specifier: str) -> str:
    candidate = specifier.strip().lower().split(";", 1)[0].strip()
    for separator in ("[", "<", ">", "=", "!", "~", " "):
        candidate = candidate.split(separator, 1)[0]
    return candidate.replace("_", "-")
