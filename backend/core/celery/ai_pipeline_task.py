import logging
import traceback
from abc import ABC, abstractmethod
from typing import Any, Union

from celery import Task
from pydantic import BaseModel

from .result import SuccessPipelineResult, ErrorPipelineResult, PipelineStatus


class AIPipelineTask(ABC, Task):
    def __init__(self):
        self.setup()

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def setup(self):
        ...

    @abstractmethod
    def predict(self, **kwargs) -> Union[SuccessPipelineResult, ErrorPipelineResult]:
        ...

    """
    Run a single prediction on the model
    """

    def run(self, **kwargs: Any) -> Any:
        try:
            result = self.predict(**kwargs)
            if isinstance(result, BaseModel):
                return result.model_dump()
            return result
        except Exception as e:
            logging.error(traceback.format_exc())
            return ErrorPipelineResult(status=PipelineStatus.ERROR, error=e).model_dump()
