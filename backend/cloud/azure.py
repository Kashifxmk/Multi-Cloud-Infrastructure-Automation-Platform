from .base import CapabilityResult, VerificationResult


class AzureSubscriptionAdapter:
    provider = "azure"
    simulated = False

    def verify(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> VerificationResult:
        try:
            from azure.core.exceptions import AzureError
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import SubscriptionClient
        except ImportError as error:
            raise RuntimeError(
                "Azure verification requires azure-identity and azure-mgmt-resource"
            ) from error

        subscription_id = account_identifier.strip()
        if not subscription_id:
            raise ValueError("Azure subscription identifier cannot be empty")
        credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=True,
        )
        try:
            subscription = SubscriptionClient(credential).subscriptions.get(subscription_id)
        except AzureError as error:
            raise RuntimeError("Azure subscription verification failed") from error

        verified_id = str(subscription.subscription_id or subscription_id)
        if verified_id.lower() != subscription_id.lower():
            raise RuntimeError("Azure subscription identity does not match the configured subscription")
        return VerificationResult(
            provider=self.provider,
            identity=verified_id,
            regions=("East US", "West Europe", "Central India"),
            capabilities=("identity",),
            simulated=False,
        )

    def capabilities(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> CapabilityResult:
        try:
            from azure.core.exceptions import AzureError
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import SubscriptionClient
        except ImportError as error:
            raise RuntimeError(
                "Azure capability discovery requires azure-identity and azure-mgmt-resource"
            ) from error
        subscription_id = account_identifier.strip()
        if not subscription_id:
            raise ValueError("Azure subscription identifier cannot be empty")
        try:
            locations = SubscriptionClient(DefaultAzureCredential(
                exclude_interactive_browser_credential=True,
            )).subscriptions.list_locations(subscription_id)
            regions = tuple(location.name for location in locations if location.name)
        except AzureError as error:
            raise RuntimeError("Azure capability discovery failed") from error
        return CapabilityResult(
            provider=self.provider,
            regions=regions,
            resource_types=("network", "compute", "storage", "database"),
            machine_types=("Standard_B1s", "Standard_B2s", "Standard_D2s_v5"),
            permissions=("Microsoft.Resources/subscriptions/read", "Microsoft.Resources/subscriptions/locations/read"),
            simulated=False,
        )
