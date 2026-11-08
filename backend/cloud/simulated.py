from .base import CapabilityResult, VerificationResult


class SimulatedProviderAdapter:
    def __init__(
        self,
        provider: str,
        regions: tuple[str, ...],
        capabilities: tuple[str, ...],
    ) -> None:
        self.provider = provider
        self.regions = regions
        self.resource_types = capabilities
        self.machine_types = ("small", "medium", "large")
        self.simulated = True

    def verify(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> VerificationResult:
        identifier = account_identifier.strip()
        if not identifier:
            raise ValueError("Account identifier cannot be empty")
        return VerificationResult(
            provider=self.provider,
            identity=identifier,
            regions=self.regions,
            capabilities=self.resource_types,
            simulated=True,
        )

    def capabilities(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> CapabilityResult:
        if not account_identifier.strip():
            raise ValueError("Account identifier cannot be empty")
        return CapabilityResult(
            provider=self.provider,
            regions=self.regions,
            resource_types=self.resource_types,
            machine_types=self.machine_types,
            permissions=tuple(f"{resource}:read" for resource in self.resource_types),
            simulated=True,
        )
