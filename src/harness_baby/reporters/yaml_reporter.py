"""Stable YAML report serialization."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml

from harness_baby.models import ScanReport


def render_yaml(report: ScanReport) -> str:
    return yaml.safe_dump(
        report.as_dict(),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def write_yaml(report: ScanReport, output_path: Path) -> None:
    """Atomically replace the report so interrupted scans do not leave partial YAML."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(render_yaml(report))
        temporary_path.replace(output_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
