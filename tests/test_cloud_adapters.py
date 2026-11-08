import pytest

from backend.cloud.aws import AwsStsAdapter
from backend.cloud.azure import AzureSubscriptionAdapter
from backend.cloud.gcp import GcpProjectAdapter
from backend.cloud.registry import get_adapter
from backend.cloud.verification import discover_capabilities, verify_account


@pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
def test_simulated_provider_adapter_returns_capabilities(provider: str):
    result = verify_account(provider, f"{provider}-demo-account")

    assert result["provider"] == provider
    assert result["identity"] == f"{provider}-demo-account"
    assert result["simulation"] is True
    assert {"network", "compute", "storage", "database"} <= set(result["capabilities"])
    assert result["regions"]


def test_unknown_provider_is_rejected():
    with pytest.raises(ValueError, match="Unsupported cloud provider"):
        get_adapter("digitalocean")


def test_empty_identifier_is_rejected():
    with pytest.raises(ValueError, match="cannot be empty"):
        verify_account("aws", " ")


@pytest.mark.parametrize("provider", ["aws", "azure", "gcp"])
def test_simulated_capability_discovery(provider: str):
    result = get_adapter(provider).capabilities(f"{provider}-demo-account")
    assert result.provider == provider
    assert result.simulated is True
    assert result.regions
    assert "network" in result.resource_types
    assert "compute:read" in result.permissions


def test_simulated_capability_service_returns_normalized_payload():
    result = discover_capabilities("gcp", "gcp-demo-project")
    assert result["provider"] == "gcp"
    assert result["simulation"] is True
    assert result["machine_types"]


@pytest.mark.parametrize(
    ("provider", "adapter_type"),
    [
        ("aws", AwsStsAdapter),
        ("azure", AzureSubscriptionAdapter),
        ("gcp", GcpProjectAdapter),
    ],
)
def test_real_mode_selects_provider_adapter(monkeypatch, provider: str, adapter_type: type):
    monkeypatch.setenv("CLOUDPILOT_PROVIDER_MODE", "real")

    assert isinstance(get_adapter(provider), adapter_type)
