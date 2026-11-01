from typing import Any


def build_architecture(configuration: dict[str, Any]) -> dict[str, Any]:
    vm_count = int(configuration.get("vm_count", 1))
    nodes = [
        {"id": "network", "type": "network", "label": "VPC / VNet", "details": {"cidr": configuration.get("vpc_cidr", "10.0.0.0/16")}},
        {"id": "public-subnet", "type": "subnet", "label": "Public subnet", "details": {"access": "public"}},
        {"id": "private-subnet", "type": "subnet", "label": "Private subnet", "details": {"access": "private"}},
        {"id": "firewall", "type": "security", "label": "Firewall", "details": {"ssh": "restricted"}},
        {"id": "load-balancer", "type": "load-balancer", "label": "Load balancer", "details": {}},
    ]
    edges = [
        {"source": "network", "target": "public-subnet"},
        {"source": "network", "target": "private-subnet"},
        {"source": "public-subnet", "target": "firewall"},
        {"source": "firewall", "target": "load-balancer"},
    ]
    for index in range(vm_count):
        node_id = f"vm-{index + 1}"
        nodes.append({"id": node_id, "type": "compute", "label": f"VM {index + 1}", "details": {"machine_type": configuration.get("machine_type", "e2-medium")}})
        edges.append({"source": "private-subnet", "target": node_id})
    if configuration.get("database_enabled") or configuration.get("template_slug") == "database":
        nodes.append({"id": "database", "type": "database", "label": "Database", "details": {"access": "private"}})
        edges.append({"source": "private-subnet", "target": "database"})
    nodes.append({"id": "storage", "type": "storage", "label": "Storage", "details": {"size_gb": configuration.get("storage_gb", 50)}})
    edges.append({"source": "private-subnet", "target": "storage"})
    return {"mode": "local", "nodes": nodes, "edges": edges}
