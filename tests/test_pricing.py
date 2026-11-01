from backend.pricing import compare, estimate


def test_estimate_has_normalized_breakdown():
    result = estimate("gcp", "asia-south1", 2, 100, True)
    assert result["is_live"] is False
    assert result["source"] == "local fixture pricing"
    assert result["monthly"] == round(sum(result["breakdown"].values()), 2)
    assert result["annual"] == round(result["monthly"] * 12, 2)


def test_compare_returns_all_supported_providers():
    result = compare({"vm_count": 1, "storage_gb": 50, "database_enabled": False})
    assert result["mode"] == "local-fixture"
    assert {item["provider"] for item in result["estimates"]} == {"aws", "gcp", "azure"}
