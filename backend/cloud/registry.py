import os

from .aws import AwsStsAdapter
from .base import CloudProviderAdapter
from .simulated import SimulatedProviderAdapter


SUPPORTED_PROVIDERS = frozenset({"aws", "azure", "gcp"})

_ADAPTERS: dict[str, CloudProviderAdapter] = {
    "aws": SimulatedProviderAdapter(
        "aws",
        ("us-east-1", "eu-west-1", "ap-south-1"),
        ("network", "compute", "storage", "database"),
    ),
    "azure": SimulatedProviderAdapter(
        "azure",
        ("East US", "West Europe", "Central India"),
        ("network", "compute", "storage", "database"),
    ),
    "gcp": SimulatedProviderAdapter(
        "gcp",
        ("us-central1", "europe-west1", "asia-south1"),
        ("network", "compute", "storage", "database"),
    ),
}


def get_adapter(provider: str) -> CloudProviderAdapter:
    normalized = provider.strip().lower()
    if os.getenv("CLOUDPILOT_PROVIDER_MODE", "simulated").strip().lower() == "real":
        if normalized == "aws":
            return AwsStsAdapter()
        raise ValueError(
            f"Real {normalized.upper()} verification is not configured; "
            "use CLOUDPILOT_PROVIDER_MODE=simulated or configure its adapter"
        )
    try:
        return _ADAPTERS[normalized]
    except KeyError as error:
        raise ValueError(f"Unsupported cloud provider: {provider}") from error
