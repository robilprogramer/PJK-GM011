from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, Any

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Any = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    total: int
    page: int
    per_page: int
