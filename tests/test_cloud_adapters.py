import pytest

from backend.cloud.registry import get_adapter
from backend.cloud.verification import verify_account


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
