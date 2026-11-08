from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VerificationResult:
    provider: str
    identity: str
    regions: tuple[str, ...]
    capabilities: tuple[str, ...]
    simulated: bool


@dataclass(frozen=True)
class CapabilityResult:
    provider: str
    regions: tuple[str, ...]
    resource_types: tuple[str, ...]
    machine_types: tuple[str, ...]
    permissions: tuple[str, ...]
    simulated: bool


class CloudProviderAdapter(Protocol):
    provider: str
    simulated: bool

    def verify(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> VerificationResult:
        """Verify account access without returning credentials."""

    def capabilities(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> CapabilityResult:
        """Discover regions, resource types, machine types, and permissions."""
