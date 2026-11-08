from backend.templates.schemas import validate_configuration


def valid_configuration() -> dict:
    return {
        "provider": "gcp",
        "region": "asia-south1",
        "vm_count": 2,
        "machine_type": "e2-medium",
        "vpc_cidr": "10.0.0.0/16",
        "public_subnets": ["10.0.1.0/24"],
        "private_subnets": ["10.0.2.0/24"],
    }


def test_valid_provider_configuration_passes():
    assert validate_configuration("web-hosting", valid_configuration()) == []


def test_invalid_cidr_and_machine_type_are_reported():
    configuration = valid_configuration()
    configuration["private_subnets"] = ["10.1.0.0/24"]
    configuration["machine_type"] = "not-a-gcp-machine"

    errors = validate_configuration("web-hosting", configuration)

    assert any("contained within" in error for error in errors)
    assert any("machine_type" in error for error in errors)


def test_overlapping_subnets_are_rejected():
    configuration = valid_configuration()
    configuration["private_subnets"] = ["10.0.1.128/25"]

    assert any("overlaps" in error for error in validate_configuration("web-hosting", configuration))
