from pathlib import Path

SUPPORTED_PROVIDERS = {"aws", "azure", "gcp"}


def terraform_directory(provider: str, root: str | Path = ".") -> Path:
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    return Path(root) / "providers" / provider
