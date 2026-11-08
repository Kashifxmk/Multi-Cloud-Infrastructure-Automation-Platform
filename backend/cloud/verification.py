from typing import Any

from .registry import get_adapter


def verify_account(
    provider: str,
    account_identifier: str,
    auth_config: dict[str, str] | None = None,
) -> dict[str, Any]:
    result = get_adapter(provider).verify(account_identifier, auth_config)
    return {
        "provider": result.provider,
        "identity": result.identity,
        "regions": list(result.regions),
        "capabilities": list(result.capabilities),
        "simulation": result.simulated,
    }


def discover_capabilities(
    provider: str,
    account_identifier: str,
    auth_config: dict[str, str] | None = None,
) -> dict[str, Any]:
    result = get_adapter(provider).capabilities(account_identifier, auth_config)
    return {
        "provider": result.provider,
        "regions": list(result.regions),
        "resource_types": list(result.resource_types),
        "machine_types": list(result.machine_types),
        "permissions": list(result.permissions),
        "simulation": result.simulated,
    }
