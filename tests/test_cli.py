from __future__ import annotations

from pathlib import Path

import yaml

from harness_baby.cli import build_parser, run


def test_cli_writes_yaml_and_prints_summary(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / "README.md").write_text("# Example\n", encoding="utf-8")
    assert run(["scan", str(tmp_path)]) == 0
    report_path = tmp_path / ".harness" / "report.yaml"
    data = yaml.safe_load(report_path.read_text(encoding="utf-8"))
    output = capsys.readouterr().out
    assert data["schema_version"] == 1
    assert data["tool"]["name"] == "harness-baby"
    assert data["tool"]["version"] == "0.1.0"
    assert "Harness Baby" in output
    assert "Score:" in output


def test_cli_rejects_missing_directory(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    assert run(["scan", str(tmp_path / "missing")]) == 2
    assert "not a directory" in capsys.readouterr().err


def test_cli_help_identifies_experimental_status() -> None:
    help_text = build_parser().format_help()

    assert "Experimental alpha software" in help_text
    assert "use at your own risk" in help_text
