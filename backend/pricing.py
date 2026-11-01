from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class PriceFixture:
    provider: str
    region: str
    vm_hourly: float
    storage_gb_monthly: float
    database_hourly: float
    network_monthly: float


FIXTURES = {
    "aws": PriceFixture("aws", "ap-south-1", 0.0416, 0.10, 0.021, 12.00),
    "gcp": PriceFixture("gcp", "asia-south1", 0.0350, 0.08, 0.018, 10.00),
    "azure": PriceFixture("azure", "centralindia", 0.0430, 0.09, 0.024, 13.00),
}


def estimate(
    provider: str,
    region: str,
    vm_count: int,
    storage_gb: int,
    database_enabled: bool,
    hours_per_month: int = 730,
) -> dict[str, Any]:
    fixture = FIXTURES[provider]
    compute = round(fixture.vm_hourly * vm_count * hours_per_month, 2)
    storage = round(fixture.storage_gb_monthly * storage_gb, 2)
    database = round(fixture.database_hourly * hours_per_month, 2) if database_enabled else 0
    networking = fixture.network_monthly
    monthly = round(compute + storage + database + networking, 2)
    return {
        "provider": provider,
        "region": region,
        "currency": "USD",
        "hourly": round(monthly / hours_per_month, 4),
        "monthly": monthly,
        "annual": round(monthly * 12, 2),
        "breakdown": {
            "compute": compute,
            "storage": storage,
            "database": database,
            "networking": networking,
        },
        "source": "local fixture pricing",
        "is_live": False,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "assumptions": [
            f"{hours_per_month} usage hours per month",
            f"{vm_count} virtual machine(s)",
            f"{storage_gb} GB storage",
            "On-demand sample rates; discounts and taxes excluded",
        ],
    }


def compare(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "local-fixture",
        "estimates": [
            estimate(
                provider,
                FIXTURES[provider].region,
                int(config.get("vm_count", 1)),
                int(config.get("storage_gb", 50)),
                bool(config.get("database_enabled", False)),
            )
            for provider in FIXTURES
        ],
    }
