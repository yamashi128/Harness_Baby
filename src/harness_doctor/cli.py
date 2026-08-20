"""Command-line interface for Harness Doctor."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from harness_doctor import __version__
from harness_doctor.models import ScanReport
from harness_doctor.reporters.yaml_reporter import write_yaml
from harness_doctor.scanner import Scanner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness-doctor")
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
    return parser


def render_summary(report: ScanReport, output_path: Path) -> str:
    lines = ["Harness Doctor", ""]
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


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "scan":
        return 2
    root = Path(args.path).expanduser().resolve()
    output_path = args.output or root / ".harness" / "report.yaml"
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    try:
        report = Scanner().scan(root)
        write_yaml(report, output_path)
    except (OSError, ValueError) as error:
        print(f"harness-doctor: error: {error}", file=sys.stderr)
        return 2
    try:
        shown_output = output_path.relative_to(Path.cwd())
    except ValueError:
        shown_output = output_path
    print(render_summary(report, shown_output))
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
