from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .authorization import organization_id_for_user
from .models import InfrastructureConfiguration, InfrastructureTemplate, User


router = APIRouter(prefix="/api/infrastructure", tags=["infrastructure"])

TEMPLATES: list[dict[str, Any]] = [
    {
        "slug": "web-hosting",
        "name": "Web Hosting",
        "description": "A secure network and compute foundation for a public web application.",
        "category": "Application",
        "difficulty": "Beginner",
        "estimated_minutes": 20,
        "resources": ["VPC/VNet", "Public subnet", "Private subnet", "VM", "Firewall", "Load balancer"],
        "providers": ["aws", "gcp", "azure"],
    },
    {
        "slug": "database",
        "name": "Database Infrastructure",
        "description": "Private database infrastructure with storage and backup configuration.",
        "category": "Data",
        "difficulty": "Intermediate",
        "estimated_minutes": 15,
        "resources": ["Private network", "Database", "Storage", "Backup policy", "Firewall"],
        "providers": ["aws", "gcp", "azure"],
    },
    {
        "slug": "application-hosting",
        "name": "Application Hosting",
        "description": "Docker-ready application hosting with reverse proxy and monitoring hooks.",
        "category": "Application",
        "difficulty": "Intermediate",
        "estimated_minutes": 25,
        "resources": ["VPC/VNet", "VM", "Docker", "Reverse proxy", "Monitoring"],
        "providers": ["aws", "gcp", "azure"],
    },
    {
        "slug": "kubernetes",
        "name": "Kubernetes Infrastructure",
        "description": "A managed Kubernetes foundation with networking and node configuration.",
        "category": "Containers",
        "difficulty": "Advanced",
        "estimated_minutes": 35,
        "resources": ["VPC/VNet", "Kubernetes cluster", "Worker nodes", "Registry", "Load balancer"],
        "providers": ["aws", "gcp", "azure"],
    },
    {
        "slug": "three-tier",
        "name": "Complete Three-Tier Application",
        "description": "Frontend, backend, and database layers separated by private networking.",
        "category": "Architecture",
        "difficulty": "Advanced",
        "estimated_minutes": 45,
        "resources": ["Frontend", "Backend", "Database", "Load balancer", "Private subnets", "Monitoring"],
        "providers": ["aws", "gcp", "azure"],
    },
    {
        "slug": "high-availability",
        "name": "High Availability Infrastructure",
        "description": "Redundant application capacity, load balancing, and recovery configuration.",
        "category": "Reliability",
        "difficulty": "Advanced",
        "estimated_minutes": 40,
        "resources": ["Multi-zone network", "Load balancer", "Replicated VMs", "Backups", "Monitoring"],
        "providers": ["aws", "gcp", "azure"],
    },
]


class ConfigurationRequest(BaseModel):
    template_slug: str = Field(min_length=2)
    configuration: dict[str, Any]


def seed_templates(db: Session) -> None:
    for definition in TEMPLATES:
        if not db.scalar(select(InfrastructureTemplate).where(InfrastructureTemplate.name == definition["name"])):
            db.add(InfrastructureTemplate(name=definition["name"], definition=definition))
    db.commit()


@router.get("/templates")
def list_templates(db: Session = Depends(get_db)):
    seed_templates(db)
    return {"templates": TEMPLATES, "mode": "local"}


@router.get("/configurations")
def list_configurations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    organization_id = organization_id_for_user(db, user)
    configurations = db.scalars(
        select(InfrastructureConfiguration).where(
            InfrastructureConfiguration.organization_id == organization_id
        )
    ).all()
    return {
        "configurations": [
            {"id": item.id, "template_id": item.template_id, "configuration": item.configuration}
            for item in configurations
        ]
    }


@router.post("/configurations", status_code=201)
def save_configuration(
    request: ConfigurationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = next((item for item in TEMPLATES if item["slug"] == request.template_slug), None)
    if not template:
        raise HTTPException(status_code=404, detail="Infrastructure template not found")
    provider = request.configuration.get("provider")
    if provider not in template["providers"]:
        raise HTTPException(status_code=422, detail="Selected provider is not supported by this template")
    required = ("region", "vm_count", "vpc_cidr")
    missing = [field for field in required if not request.configuration.get(field)]
    if missing:
        raise HTTPException(status_code=422, detail={"missing_fields": missing})
    organization_id = organization_id_for_user(db, user)
    template_row = db.scalar(
        select(InfrastructureTemplate).where(InfrastructureTemplate.name == template["name"])
    )
    item = InfrastructureConfiguration(
        organization_id=organization_id,
        template_id=template_row.id if template_row else None,
        configuration={"template_slug": request.template_slug, **request.configuration},
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "configuration": item.configuration, "mode": "local"}
