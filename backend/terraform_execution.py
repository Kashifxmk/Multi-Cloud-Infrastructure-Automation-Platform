import os
import re
import subprocess
import tempfile
from pathlib import Path
from collections.abc import Callable
from typing import Any

from .terraform_generator import generate_files


class TerraformExecutionError(RuntimeError):
    """Raised when a Terraform plan cannot be completed."""


def plan(
    configuration: dict[str, Any],
    executable: str = "terraform",
    on_output: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if os.getenv("CLOUDPILOT_TERRAFORM_PLAN_ENABLED", "").strip().lower() != "true":
        raise TerraformExecutionError("Terraform plan execution is disabled")

    files = generate_files(configuration)
    with tempfile.TemporaryDirectory(prefix="cloudpilot-plan-") as directory:
        worktree = Path(directory)
        for filename, content in files.items():
            if filename.endswith(".tf"):
                (worktree / filename).write_text(content, encoding="utf-8")

        _run(
            executable,
            worktree,
            "init",
            "-backend=false",
            "-input=false",
            on_output=on_output,
        )
        result = _run(
            executable,
            worktree,
            "plan",
            "-refresh=false",
            "-input=false",
            "-lock=false",
            "-no-color",
            *variable_arguments(configuration),
            on_output=on_output,
        )
        return {
            "mode": "real-plan",
            "message": "Terraform plan completed; no resources were applied.",
            "output": result.stdout.strip(),
        }


def variable_arguments(configuration: dict[str, Any]) -> list[str]:
    allowed = (
        "project_name",
        "region",
        "vm_count",
        "machine_type",
        "vpc_cidr",
        "storage_gb",
        "database_enabled",
        "ami_id",
        "boot_image",
        "image_publisher",
        "image_offer",
        "image_sku",
        "ssh_public_key",
    )
    arguments: list[str] = []
    for key in allowed:
        value = configuration.get(key)
        if value is not None:
            arguments.extend(("-var", f"{key}={value}"))
    return arguments


def sanitize_output(line: str) -> str:
    return re.sub(
        r"(?i)(password|secret|token|private_key)\s*=\s*[^\s,]+",
        r"\1=[REDACTED]",
        line,
    )[:4000]


def _run(
    executable: str,
    directory: Path,
    *arguments: str,
    on_output: Callable[[str], None] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [executable, *arguments]
    try:
        process = subprocess.Popen(
            command,
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output: list[str] = []
        assert process.stdout is not None
        for line in process.stdout:
            clean_line = sanitize_output(line.rstrip())
            output.append(clean_line)
            if on_output:
                on_output(clean_line)
        return_code = process.wait(timeout=300)
    except (OSError, subprocess.TimeoutExpired) as error:
        if "process" in locals() and process.poll() is None:
            process.kill()
        raise TerraformExecutionError("Terraform command could not complete") from error
    result = subprocess.CompletedProcess(command, return_code, "\n".join(output), "")
    if result.returncode:
        detail = result.stdout.strip() or "Terraform command failed"
        raise TerraformExecutionError(detail)
    return result
