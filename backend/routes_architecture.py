from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .architecture import build_architecture


router = APIRouter(prefix="/api/architecture", tags=["architecture"])


class ArchitectureRequest(BaseModel):
    provider: str = "gcp"
    region: str = "asia-south1"
    vm_count: int = Field(default=1, ge=1, le=20)
    machine_type: str = "e2-medium"
    vpc_cidr: str = "10.0.0.0/16"
    storage_gb: int = Field(default=50, ge=1)
    database_enabled: bool = False
    template_slug: str | None = None


@router.post("/generate")
def generate_architecture(request: ArchitectureRequest) -> dict[str, Any]:
    return build_architecture(request.model_dump())
