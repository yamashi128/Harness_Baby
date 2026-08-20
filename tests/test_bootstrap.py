from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from harness_doctor.bootstrap import (
    GENERATED_PATHS,
    BootstrapStatus,
    apply_bootstrap,
    plan_bootstrap,
)
from harness_doctor.cli import run


def test_init_previews_without_creating_target(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "new-project"

    assert run(["init", str(target), "--project-name", "Example Project"]) == 0

    assert not target.exists()
    output = capsys.readouterr().out
    assert "State: PREVIEW" in output
    assert "No files were written" in output
    assert list(GENERATED_PATHS) == [
        line.strip() for line in output.splitlines() if line.startswith("  ")
    ]


def test_init_applies_generic_skeleton_to_missing_target(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "new-project"

    assert (
        run(
            [
                "init",
                str(target),
                "--project-name",
                "Example Project",
                "--apply",
            ]
        )
        == 0
    )

    assert {
        path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()
    } == set(GENERATED_PATHS)
    manifest = yaml.safe_load((target / ".agent-readiness.yaml").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["template"] == {"id": "generic-agent-ready", "version": 1}
    assert manifest["project"]["name"] == "Example Project"
    assert manifest["generated_files"] == list(GENERATED_PATHS)
    assert "State: CREATED" in capsys.readouterr().out


def test_init_allows_an_existing_empty_git_repository(tmp_path: Path) -> None:
    target = tmp_path / "new-project"
    git_directory = target / ".git"
    git_directory.mkdir(parents=True)

    assert run(["init", str(target), "--apply"]) == 0

    assert git_directory.is_dir()
    assert (target / "AGENTS.md").is_file()


def test_init_refuses_unexpected_content_without_overwriting(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "existing-project"
    target.mkdir()
    existing = target / "notes.txt"
    existing.write_text("keep me\n", encoding="utf-8")

    assert run(["init", str(target), "--apply"]) == 2

    assert existing.read_text(encoding="utf-8") == "keep me\n"
    assert not (target / "AGENTS.md").exists()
    error = capsys.readouterr().err
    assert "unexpected path: notes.txt" in error
    assert "keep me" not in error


def test_init_refuses_partial_skeleton(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "partial-project"
    preview = plan_bootstrap(target)
    target.mkdir()
    first = preview.files[0]
    (target / first.relative_path).write_text(first.content, encoding="utf-8")

    assert run(["init", str(target), "--apply"]) == 2

    assert {path.name for path in target.iterdir()} == {Path(first.relative_path).name}
    assert "missing generated path" in capsys.readouterr().err


def test_init_refuses_modified_generated_file(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "modified-project"
    assert run(["init", str(target), "--apply"]) == 0
    capsys.readouterr()
    agents = target / "AGENTS.md"
    agents.write_text("human-owned content\n", encoding="utf-8")

    assert run(["init", str(target), "--apply"]) == 2

    assert agents.read_text(encoding="utf-8") == "human-owned content\n"
    assert "modified generated file: AGENTS.md" in capsys.readouterr().err


def test_init_is_idempotent_after_readiness_scan(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "loop-project"
    assert run(["init", str(target), "--apply"]) == 0
    capsys.readouterr()
    modification_times = {
        relative: (target / relative).stat().st_mtime_ns for relative in GENERATED_PATHS
    }

    assert run(["scan", str(target)]) == 0
    report = yaml.safe_load((target / ".harness" / "report.yaml").read_text(encoding="utf-8"))
    assert report["schema_version"] == 1
    assert report["checks"]["documentation"]["status"] == "pass"
    assert report["checks"]["agent_context"]["status"] == "pass"
    capsys.readouterr()

    assert run(["init", str(target), "--apply"]) == 0

    assert {
        relative: (target / relative).stat().st_mtime_ns for relative in GENERATED_PATHS
    } == modification_times
    assert "State: UNCHANGED" in capsys.readouterr().out
    assert plan_bootstrap(target).status is BootstrapStatus.UNCHANGED


def test_init_rejects_multiline_project_name(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "new-project"

    assert run(["init", str(target), "--project-name", "bad\nname", "--apply"]) == 2

    assert not target.exists()
    assert "single printable line" in capsys.readouterr().err


def test_apply_rolls_back_paths_created_before_a_write_failure(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "rollback-project"
    original_open = Path.open
    exclusive_open_count = 0

    class FailingWriter:
        def __init__(self, stream) -> None:  # type: ignore[no-untyped-def]
            self.stream = stream

        def __enter__(self):  # type: ignore[no-untyped-def]
            self.stream.__enter__()
            return self

        def write(self, value: str) -> None:
            self.stream.write(value[:1])
            raise OSError("synthetic write failure")

        def __exit__(self, *args) -> None:  # type: ignore[no-untyped-def]
            self.stream.__exit__(*args)

    def fail_second_exclusive_open(self: Path, *args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal exclusive_open_count
        if args and args[0] == "x":
            exclusive_open_count += 1
            stream = original_open(self, *args, **kwargs)
            if exclusive_open_count == 2:
                return FailingWriter(stream)
            return stream
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_second_exclusive_open)

    with pytest.raises(OSError, match="synthetic write failure"):
        apply_bootstrap(target)

    assert not target.exists()
