"""Terraform structure and safe validation-readiness checks."""

from __future__ import annotations

import shutil
from pathlib import Path

from harness_doctor.checks.base import Check
from harness_doctor.models import CheckResult, ScanContext, Status


class TerraformValidationCheck(Check):
    id = "validation"
    category = "validation"

    def run(self, context: ScanContext) -> CheckResult:
        if "terraform" not in context.detected_stacks:
            return CheckResult(
                self.id,
                self.category,
                Status.SKIP,
                {"reason": "Terraform stack not detected"},
            )

        terraform_files = sorted(
            context.relative(path) for path in context.paths_with_suffix(".tf")
        )
        module_dirs = sorted(
            {
                Path(relative_path).parent.as_posix()
                for relative_path in map(context.relative, context.paths_with_suffix(".tf"))
            }
        )
        binary = shutil.which("terraform")
        analyzer_configs = sorted(
            context.relative(path)
            for path in context.files
            if path.name in {".checkov.yml", ".checkov.yaml", ".tfsec.yml", ".tfsec.yaml"}
            or ".tfsec" in path.parts
        )
        evidence = {
            "terraform_files": terraform_files,
            "terraform_file_count": len(terraform_files),
            "module_directories": module_dirs,
            "terraform_binary_available": binary is not None,
            "terraform_fmt_executable": binary is not None,
            "terraform_validate_executable": binary is not None,
            "static_analysis_configs": analyzer_configs,
            "commands_executed": [],
        }
        if binary:
            evidence["reason"] = (
                "Terraform is installed; commands were not executed because scans are read-only"
            )
            return CheckResult(self.id, self.category, Status.PASS, evidence)
        evidence["reason"] = "Terraform files detected but terraform executable is unavailable"
        return CheckResult(self.id, self.category, Status.WARN, evidence)
