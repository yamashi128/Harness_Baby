"""Command-line interface for Harness Baby."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from harness_baby import __version__
from harness_baby.bootstrap import (
    BootstrapConflictError,
    BootstrapPlan,
    BootstrapStatus,
    apply_bootstrap,
    plan_bootstrap,
)
from harness_baby.models import ScanReport
from harness_baby.reporters.yaml_reporter import write_yaml
from harness_baby.scanner import Scanner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness-baby")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan_parser = subparsers.add_parser("scan", help="scan a repository without modifying it")
    scan_parser.add_argument("path", nargs="?", default=".", help="repository path (default: .)")
    scan_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="report path (default: <repository>/.harness/report.yaml)",
    )
    init_parser = subparsers.add_parser(
        "init", help="preview or create a minimal harness in an empty directory"
    )
    init_parser.add_argument("path", nargs="?", default=".", help="target path (default: .)")
    init_parser.add_argument(
        "--project-name",
        help="project name (default: target directory name)",
    )
    init_parser.add_argument(
        "--apply",
        action="store_true",
        help="create the planned files; preview is the default",
    )
    return parser


def render_summary(report: ScanReport, output_path: Path) -> str:
    lines = ["Harness Baby", ""]
    for check_id, check in report.checks.items():
        label = check_id.replace("_", " ").title()
        lines.append(f"{label:<18} {str(check['status']).upper()}")
    lines.extend(
        [
            "",
            f"Score: {report.summary['score']}/100",
            "",
            "Report written to:",
            output_path.as_posix(),
        ]
    )
    return "\n".join(lines)


def render_bootstrap(plan: BootstrapPlan, applied: bool) -> str:
    if plan.status is BootstrapStatus.UNCHANGED:
        state = "UNCHANGED"
        note = "The complete skeleton already matches; no files were rewritten."
    elif applied:
        state = "CREATED"
        note = "Next: fill the TODOs, then run `harness-baby scan .`."
    else:
        state = "PREVIEW"
        note = "No files were written. Re-run with `--apply` to create this skeleton."
    lines = [
        "Harness skeleton",
        "",
        f"Target: {plan.target.as_posix()}",
        f"Project: {plan.project_name}",
        f"State: {state}",
        "",
        "Files:",
    ]
    lines.extend(f"  {item.relative_path}" for item in plan.files)
    lines.extend(["", note])
    return "\n".join(lines)


def _run_scan(args: argparse.Namespace) -> int:
    path = str(args.path)
    requested_output = args.output
    root = Path(path).expanduser().resolve()
    output_path = requested_output or root / ".harness" / "report.yaml"
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    report = Scanner().scan(root)
    write_yaml(report, output_path)
    try:
        shown_output = output_path.relative_to(Path.cwd())
    except ValueError:
        shown_output = output_path
    print(render_summary(report, shown_output))
    return 0


def _run_init(args: argparse.Namespace) -> int:
    path = str(args.path)
    project_name = args.project_name
    should_apply = bool(args.apply)
    plan = plan_bootstrap(path, project_name)
    if plan.status is BootstrapStatus.CONFLICT:
        raise BootstrapConflictError(plan.conflicts)
    if should_apply:
        before = plan.status
        plan = apply_bootstrap(path, project_name)
        if before is BootstrapStatus.CREATE:
            plan = BootstrapPlan(
                plan.target,
                plan.project_name,
                plan.files,
                BootstrapStatus.CREATE,
            )
    print(render_bootstrap(plan, should_apply))
    return 0


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "scan":
            return _run_scan(args)
        if args.command == "init":
            return _run_init(args)
        return 2
    except (OSError, ValueError) as error:
        print(f"harness-baby: error: {error}", file=sys.stderr)
        return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
