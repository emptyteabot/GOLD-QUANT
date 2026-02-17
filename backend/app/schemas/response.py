"""通用响应schemas"""
from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime


class APIResponse(BaseModel):
    """统一API响应格式"""
    code: int = 200
    message: str = "Success"
    data: Optional[Any] = None
    timestamp: datetime = datetime.now()


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int
    message: str
    error: Optional[str] = None
    timestamp: datetime = datetime.now()
