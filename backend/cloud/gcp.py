import os

from .base import CapabilityResult, VerificationResult


class GcpProjectAdapter:
    provider = "gcp"
    simulated = False

    def verify(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> VerificationResult:
        try:
            import google.auth
            from google.api_core.exceptions import GoogleAPIError
            from google.cloud import resourcemanager_v3
        except ImportError as error:
            raise RuntimeError(
                "GCP verification requires google-auth and google-cloud-resource-manager"
            ) from error

        project_id = account_identifier.strip() or os.getenv("GOOGLE_PROJECT", "").strip()
        if not project_id:
            raise ValueError("GCP project identifier cannot be empty")
        try:
            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            project = resourcemanager_v3.ProjectsClient(credentials=credentials).get_project(
                name=f"projects/{project_id}"
            )
        except GoogleAPIError as error:
            raise RuntimeError("GCP project verification failed") from error
        except google.auth.exceptions.DefaultCredentialsError as error:
            raise RuntimeError("GCP application credentials are not configured") from error

        verified_id = str(project.project_id or project_id)
        if verified_id != project_id:
            raise RuntimeError("GCP project identity does not match the configured project")
        return VerificationResult(
            provider=self.provider,
            identity=verified_id,
            regions=("us-central1", "europe-west1", "asia-south1"),
            capabilities=("identity",),
            simulated=False,
        )

    def capabilities(
        self, account_identifier: str, auth_config: dict[str, str] | None = None
    ) -> CapabilityResult:
        try:
            import google.auth
            from google.api_core.exceptions import GoogleAPIError
            from google.cloud import compute_v1
        except ImportError as error:
            raise RuntimeError(
                "GCP capability discovery requires google-auth and google-cloud-compute"
            ) from error
        project_id = account_identifier.strip() or os.getenv("GOOGLE_PROJECT", "").strip()
        if not project_id:
            raise ValueError("GCP project identifier cannot be empty")
        try:
            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            regions = tuple(
                item.name
                for item in compute_v1.RegionsClient(credentials=credentials).list(
                    project=project_id
                )
                if item.name
            )
        except GoogleAPIError as error:
            raise RuntimeError("GCP capability discovery failed") from error
        except google.auth.exceptions.DefaultCredentialsError as error:
            raise RuntimeError("GCP application credentials are not configured") from error
        return CapabilityResult(
            provider=self.provider,
            regions=regions,
            resource_types=("network", "compute", "storage", "database"),
            machine_types=("e2-micro", "e2-medium", "n2-standard-2"),
            permissions=("resourcemanager.projects.get", "compute.regions.list", "compute.machineTypes.list"),
            simulated=False,
        )
