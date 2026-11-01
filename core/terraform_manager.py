import json
import subprocess
from pathlib import Path
from typing import Any


class TerraformError(RuntimeError):
    """Raised when Terraform returns a non-zero status."""


class TerraformManager:
    def __init__(self, directory: str | Path, executable: str = "terraform") -> None:
        self.directory = Path(directory)
        self.executable = executable

    def run(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [self.executable, *args],
            cwd=self.directory,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise TerraformError(result.stderr.strip() or result.stdout.strip())
        return result

    def init(self) -> subprocess.CompletedProcess[str]:
        return self.run("init", "-input=false")

    def plan(self, variables: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return self.run("plan", "-input=false", *self._variable_args(variables))

    def apply(self, variables: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return self.run("apply", "-input=false", "-auto-approve", *self._variable_args(variables))

    def destroy(self, variables: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return self.run("destroy", "-input=false", "-auto-approve", *self._variable_args(variables))

    @staticmethod
    def _variable_args(variables: dict[str, str] | None) -> list[str]:
        return [f"-var={key}={value}" for key, value in (variables or {}).items()]

    def outputs(self) -> dict[str, Any]:
        result = self.run("output", "-json")
        return json.loads(result.stdout or "{}")
