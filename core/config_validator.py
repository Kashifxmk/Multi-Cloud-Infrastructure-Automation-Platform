from typing import Any

SUPPORTED_PROVIDERS = {"aws", "azure", "gcp"}


class ConfigurationError(ValueError):
    """Raised when a CloudPilot configuration is invalid."""


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    project = config.get("project")
    cloud = config.get("cloud")
    if not isinstance(project, dict) or not project.get("name") or not project.get("environment"):
        errors.append("project.name and project.environment are required")
    if not isinstance(cloud, dict):
        errors.append("cloud.provider and cloud.region are required")
    else:
        provider = cloud.get("provider")
        if provider not in SUPPORTED_PROVIDERS:
            errors.append(f"cloud.provider must be one of: {', '.join(sorted(SUPPORTED_PROVIDERS))}")
        if not cloud.get("region"):
            errors.append("cloud.region is required")
    compute = config.get("compute", {})
    if compute.get("enabled") and (not compute.get("name") or not compute.get("machine_type")):
        errors.append("enabled compute requires compute.name and compute.machine_type")
    security = config.get("security", {})
    if security.get("allow_ssh") and not security.get("allowed_ssh_cidrs"):
        errors.append("security.allowed_ssh_cidrs is required when SSH is enabled")
    return errors


def require_valid_config(config: dict[str, Any]) -> None:
    errors = validate_config(config)
    if errors:
        raise ConfigurationError("; ".join(errors))
