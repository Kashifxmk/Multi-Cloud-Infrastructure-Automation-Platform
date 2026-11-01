from core.config_validator import validate_config


def test_valid_config():
    assert validate_config({"project": {"name": "x", "environment": "dev"}, "cloud": {"provider": "gcp", "region": "x"}}) == []


def test_invalid_provider():
    errors = validate_config({"project": {"name": "x", "environment": "dev"}, "cloud": {"provider": "nope", "region": "x"}})
    assert "cloud.provider must be one of: aws, azure, gcp" in errors


def test_ssh_requires_cidrs():
    errors = validate_config({"project": {"name": "x", "environment": "dev"}, "cloud": {"provider": "aws", "region": "x"}, "security": {"allow_ssh": True}})
    assert "security.allowed_ssh_cidrs is required when SSH is enabled" in errors
