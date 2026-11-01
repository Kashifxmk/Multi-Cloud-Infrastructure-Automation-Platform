from core.provider_manager import terraform_directory


def test_provider_directory():
    assert terraform_directory("aws", "root").as_posix() == "root/providers/aws"
