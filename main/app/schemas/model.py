from pydantic import BaseModel
from typing import Optional


class ModelInfoResponse(BaseModel):
    model_id: str
    display_name: str
    provider: str
    context_window: int
    is_free: bool
    is_active: bool
    description: str
    tags: list[str]


class ModelListResponse(BaseModel):
    models: list[ModelInfoResponse]
    default_model: str
    total: int
    total_active: int
