from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VerificationResult:
    provider: str
    identity: str
    regions: tuple[str, ...]
    capabilities: tuple[str, ...]
    simulated: bool


class CloudProviderAdapter(Protocol):
    provider: str
    simulated: bool

    def verify(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> VerificationResult:
        """Verify account access without returning credentials."""
