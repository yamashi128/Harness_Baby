from __future__ import annotations

from pathlib import Path

from harness_baby.models import Status
from harness_baby.scanner import Scanner
from harness_baby.scoring import calculate_score


def write(root: Path, relative: str, content: str = "") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def scan(root: Path):  # type: ignore[no-untyped-def]
    return Scanner().scan(root)


def test_empty_repository(tmp_path: Path) -> None:
    report = scan(tmp_path)
    assert report.project["detected_stacks"] == []
    assert report.checks["repository"]["status"] == "fail"
    assert report.checks["testing"]["status"] == "skip"


def test_python_repository(tmp_path: Path) -> None:
    write(
        tmp_path,
        "pyproject.toml",
        """[project]
dependencies = ["pytest", "ruff", "black"]
[tool.pytest.ini_options]
[tool.ruff]
[tool.black]
""",
    )
    write(tmp_path, "tests/test_app.py", "def test_ok():\n    assert True\n")
    report = scan(tmp_path)
    assert report.project["detected_stacks"] == ["python"]
    assert report.checks["testing"]["status"] == "pass"
    assert report.checks["linting"]["status"] == "pass"
    assert report.checks["formatting"]["status"] == "pass"


def test_terraform_repository(tmp_path: Path) -> None:
    write(tmp_path, "main.tf", 'terraform { required_version = ">= 1.6" }\n')
    write(tmp_path, "modules/network/variables.tf", 'variable "name" { type = string }\n')
    write(tmp_path, ".tflint.hcl", "config { disabled_by_default = false }\n")
    report = scan(tmp_path)
    evidence = report.checks["validation"]["evidence"]
    assert report.project["detected_stacks"] == ["terraform"]
    assert evidence["terraform_file_count"] == 2
    assert evidence["commands_executed"] == []
    assert report.checks["linting"]["status"] == "pass"


def test_github_actions_repository(tmp_path: Path) -> None:
    write(
        tmp_path,
        ".github/workflows/ci.yml",
        """name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
      - run: ruff check .
""",
    )
    report = scan(tmp_path)
    assert "github_actions" in report.project["detected_stacks"]
    assert report.checks["ci"]["status"] == "pass"
    assert report.checks["security"]["status"] == "pass"


def test_multiple_stack_repository(tmp_path: Path) -> None:
    write(
        tmp_path, "pyproject.toml", "[tool.ruff]\n[tool.ruff.format]\n[tool.pytest.ini_options]\n"
    )
    write(tmp_path, "main.tf", "terraform {}\n")
    write(tmp_path, ".tflint.hcl", "config {}\n")
    write(
        tmp_path,
        ".github/workflows/ci.yaml",
        (
            "jobs:\n  ci:\n    steps:\n"
            "      - run: pytest\n"
            "      - run: ruff check .\n"
            "      - run: terraform validate\n"
        ),
    )
    report = scan(tmp_path)
    assert report.project["detected_stacks"] == ["python", "terraform", "github_actions"]
    assert report.checks["ci"]["status"] == "pass"
    assert report.checks["linting"]["status"] == "pass"


def test_missing_agents_md(tmp_path: Path) -> None:
    write(tmp_path, "README.md", "# Example\n")
    report = scan(tmp_path)
    assert report.checks["agent_context"]["status"] == "warn"
    assert report.checks["agent_context"]["evidence"]["agents_md"] is False


def test_missing_lint_configuration(tmp_path: Path) -> None:
    write(tmp_path, "app.py", "print('hello')\n")
    report = scan(tmp_path)
    assert report.checks["linting"]["status"] == "fail"


def test_missing_ci(tmp_path: Path) -> None:
    write(tmp_path, "app.py", "print('hello')\n")
    report = scan(tmp_path)
    assert report.checks["ci"]["status"] == "warn"
    assert report.checks["ci"]["evidence"]["github_actions"] is False


def test_score_ignores_skips_and_supports_weights() -> None:
    from harness_baby.models import CheckResult

    results = [
        CheckResult("a", "a", Status.PASS),
        CheckResult("b", "b", Status.WARN),
        CheckResult("c", "c", Status.FAIL),
        CheckResult("d", "d", Status.SKIP),
    ]
    assert calculate_score(results) == 50
    assert calculate_score(results, {"a": 2.0, "b": 1.0, "c": 1.0}) == 62


def test_secret_finding_never_contains_secret_value(tmp_path: Path) -> None:
    secret = "synthetic-test-value"
    write(tmp_path, ".github/workflows/ci.yml", f"env:\n  API_TOKEN: {secret}\n")
    report = scan(tmp_path)
    security = report.checks["security"]
    assert security["status"] == "fail"
    assert secret not in repr(report.as_dict())
    assert security["evidence"]["potential_hardcoded_secrets"][0]["line"] == 2


def test_secret_reference_is_safe(tmp_path: Path) -> None:
    write(tmp_path, ".github/workflows/ci.yml", "env:\n  API_TOKEN: ${{ secrets.API_TOKEN }}\n")
    report = scan(tmp_path)
    assert report.checks["security"]["status"] == "pass"


def test_github_oidc_permission_is_not_a_secret(tmp_path: Path) -> None:
    write(
        tmp_path,
        ".github/workflows/release.yml",
        "permissions:\n  id-token: write # Required for trusted publishing\n",
    )
    report = scan(tmp_path)
    assert report.checks["security"]["status"] == "pass"
