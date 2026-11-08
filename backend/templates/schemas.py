from ipaddress import ip_network
from typing import Any


SCHEMA_VERSION = 1
SUPPORTED_PROVIDERS = frozenset({"aws", "azure", "gcp"})
TEMPLATE_RESOURCE_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "web-hosting": ("network", "compute"),
    "database": ("network", "database", "storage"),
    "application-hosting": ("network", "compute"),
    "kubernetes": ("network", "compute"),
    "three-tier": ("network", "compute", "database"),
    "high-availability": ("network", "compute"),
}
PROVIDER_MACHINE_TYPES = {
    "aws": frozenset({"small", "medium", "large", "t3.micro", "t3.medium", "m6i.large"}),
    "azure": frozenset({"small", "medium", "large", "Standard_B1s", "Standard_B2s", "Standard_D2s_v5"}),
    "gcp": frozenset({"small", "medium", "large", "e2-micro", "e2-medium", "n2-standard-2"}),
}


def template_schema(slug: str) -> dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "required": ["provider", "region", "vm_count", "machine_type", "vpc_cidr"],
        "properties": {
            "provider": {"type": "string", "enum": sorted(SUPPORTED_PROVIDERS)},
            "region": {"type": "string", "min_length": 2},
            "vm_count": {"type": "integer", "minimum": 1, "maximum": 100},
            "machine_type": {"type": "string", "min_length": 2},
            "vpc_cidr": {"type": "cidr", "private_only": True},
            "public_subnets": {"type": "array", "items": {"type": "cidr"}},
            "private_subnets": {"type": "array", "items": {"type": "cidr"}},
            "storage_gb": {"type": "integer", "minimum": 1, "maximum": 10240},
            "database_enabled": {"type": "boolean"},
        },
        "resource_requirements": list(TEMPLATE_RESOURCE_REQUIREMENTS.get(slug, ())),
    }


def validate_configuration(
    template_slug: str | None,
    configuration: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    provider = configuration.get("provider")
    if provider not in SUPPORTED_PROVIDERS:
        errors.append("provider must be aws, gcp, or azure")
    region = configuration.get("region")
    if not isinstance(region, str) or len(region.strip()) < 2:
        errors.append("region must be a non-empty string")
    vm_count = configuration.get("vm_count")
    if not isinstance(vm_count, int) or isinstance(vm_count, bool) or not 1 <= vm_count <= 100:
        errors.append("vm_count must be an integer between 1 and 100")
    machine_type = configuration.get("machine_type")
    if not isinstance(machine_type, str) or len(machine_type.strip()) < 2:
        errors.append("machine_type must be a non-empty string")
    elif provider in PROVIDER_MACHINE_TYPES and machine_type not in PROVIDER_MACHINE_TYPES[provider]:
        errors.append(f"machine_type is not supported by {provider}")
    vpc_cidr = _parse_network(configuration.get("vpc_cidr"), "vpc_cidr", errors)
    if vpc_cidr and not vpc_cidr.is_private:
        errors.append("vpc_cidr must be a private network")
    public_subnets = _parse_subnets(configuration.get("public_subnets", []), "public_subnets", errors)
    private_subnets = _parse_subnets(configuration.get("private_subnets", []), "private_subnets", errors)
    all_subnets = public_subnets + private_subnets
    for index, subnet in enumerate(all_subnets):
        if vpc_cidr and not subnet.subnet_of(vpc_cidr):
            errors.append(f"subnet {index} must be contained within vpc_cidr")
        if any(subnet.overlaps(other) for other_index, other in enumerate(all_subnets) if index != other_index):
            errors.append(f"subnet {index} overlaps another subnet")
    storage_gb = configuration.get("storage_gb")
    if storage_gb is not None and (
        not isinstance(storage_gb, int) or isinstance(storage_gb, bool) or not 1 <= storage_gb <= 10240
    ):
        errors.append("storage_gb must be an integer between 1 and 10240")
    database_enabled = configuration.get("database_enabled")
    if database_enabled is not None and not isinstance(database_enabled, bool):
        errors.append("database_enabled must be boolean")
    if template_slug and template_slug not in TEMPLATE_RESOURCE_REQUIREMENTS:
        errors.append("unknown infrastructure template")
    return errors


def _parse_network(value: Any, field: str, errors: list[str]):
    if not isinstance(value, str):
        errors.append(f"{field} must be a CIDR string")
        return None
    try:
        return ip_network(value, strict=False)
    except ValueError:
        errors.append(f"{field} must be a valid CIDR network")
        return None


def _parse_subnets(value: Any, field: str, errors: list[str]):
    if not isinstance(value, list):
        errors.append(f"{field} must be a list of CIDR strings")
        return []
    networks = []
    for index, item in enumerate(value):
        network = _parse_network(item, f"{field}[{index}]", errors)
        if network:
            networks.append(network)
    return networks
