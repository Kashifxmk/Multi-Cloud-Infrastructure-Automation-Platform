from backend.architecture import build_architecture


def test_architecture_contains_network_compute_and_database():
    result = build_architecture(
        {"vm_count": 2, "database_enabled": True, "vpc_cidr": "10.0.0.0/16"}
    )
    ids = {node["id"] for node in result["nodes"]}
    assert {"network", "private-subnet", "vm-1", "vm-2", "database", "storage"} <= ids
    assert {"source": "private-subnet", "target": "database"} in result["edges"]


def test_architecture_scales_compute_nodes():
    result = build_architecture({"vm_count": 4})
    assert len([node for node in result["nodes"] if node["type"] == "compute"]) == 4
