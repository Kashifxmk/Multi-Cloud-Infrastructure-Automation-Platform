from backend.terraform_generator import generate_files, preview


def test_generates_provider_specific_files():
    files = generate_files(
        {
            "provider": "gcp",
            "region": "asia-south1",
            "vm_count": 2,
            "machine_type": "e2-medium",
            "vpc_cidr": "10.0.0.0/16",
        }
    )
    assert set(files) == {"main.tf", "variables.tf", "outputs.tf", "terraform.tfvars.example"}
    assert 'provider "google"' in files["main.tf"]
    assert "count = var.vm_count" in files["main.tf"]


def test_preview_is_explicitly_local():
    result = preview({"provider": "aws", "region": "ap-south-1"})
    assert result["mode"] == "local-preview"
    assert result["backend"] == "disabled"
    assert "not initialized" in result["message"]
