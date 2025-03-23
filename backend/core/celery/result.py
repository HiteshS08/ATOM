from enum import Enum
from typing import Any

from pydantic import BaseModel


class PipelineStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class ErrorPipelineResult(BaseModel):
    status: PipelineStatus = PipelineStatus.ERROR
    error: Any


class SuccessPipelineResult(BaseModel):
    status: PipelineStatus = PipelineStatus.SUCCESS
    data: Any
