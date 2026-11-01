from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .terraform_generator import preview


router = APIRouter(prefix="/api/terraform", tags=["terraform"])


class TerraformRequest(BaseModel):
    provider: str
    region: str
    vm_count: int = Field(default=1, ge=1, le=100)
    machine_type: str = "e2-medium"
    vpc_cidr: str = "10.0.0.0/16"
    project_name: str = "cloudpilot"


@router.post("/generate-preview")
def generate_preview(request: TerraformRequest) -> dict[str, Any]:
    try:
        return preview(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
