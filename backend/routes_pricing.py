from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .pricing import compare


router = APIRouter(prefix="/api/pricing", tags=["pricing"])


class PricingRequest(BaseModel):
    vm_count: int = Field(default=1, ge=1, le=100)
    storage_gb: int = Field(default=50, ge=1, le=100000)
    database_enabled: bool = False


@router.post("/compare")
def compare_pricing(request: PricingRequest) -> dict[str, Any]:
    return compare(request.model_dump())
