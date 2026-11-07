from .base import VerificationResult


class SimulatedProviderAdapter:
    def __init__(
        self,
        provider: str,
        regions: tuple[str, ...],
        capabilities: tuple[str, ...],
    ) -> None:
        self.provider = provider
        self.regions = regions
        self.capabilities = capabilities
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
            capabilities=self.capabilities,
            simulated=True,
        )
