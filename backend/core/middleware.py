import json
import logging
import time
import uuid
from typing import Any

from celery import Task
from celery.signals import before_task_publish, task_prerun
from fastapi import Request
from faststream import BaseMiddleware
from faststream.broker.message import StreamMessage
from starlette.middleware.base import BaseHTTPMiddleware

from core.faststream_core import MsgBaseModel
from .context_var import correlation_id_ctx_var


# Create a context variable to store correlation ID


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get('x-correlation-id', str(uuid.uuid4()))
        # Set correlation ID in context
        correlation_id_ctx_var.set(correlation_id)
        response = await call_next(request)
        response.headers['x-correlation-id'] = correlation_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log request
        await LoggingMiddleware._log_request(request)

        # Record start time
        start_time = time.time()

        # Get response
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        await self._log_response(response, duration)

        return response

    @staticmethod
    async def _log_request(request: Request):
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            if request.headers.get("content-type") == "application/json":
                try:
                    body = await request.json()
                except:
                    body = "(unable to parse request body)"

        log_msg = f"Request: method={request.method} url={str(request.url)}"
        if body:
            log_msg += f" body={json.dumps(body)}"
        logging.debug(log_msg)

    @staticmethod
    async def _log_response(response, duration):
        log_msg = f"Response: status={response.status_code} duration_ms={round(duration * 1000, 2)}"
        logging.debug(log_msg)


class FaststreamLoggingMiddleware(BaseMiddleware):
    async def on_consume(
            self,
            msg: "StreamMessage[Any]",
    ) -> "StreamMessage[Any]":
        if isinstance(msg, StreamMessage):
            decoded_msg = await msg.decode()
            if isinstance(decoded_msg, dict):
                correlation_id = decoded_msg.get("correlation_id", msg.correlation_id)
            else:
                correlation_id = getattr(decoded_msg, "correlation_id", msg.correlation_id)
            correlation_id_ctx_var.set(correlation_id)
        return msg

    async def after_processed(self, exc_type, exc_val, exc_tb) -> bool:
        # TODO implement debug and tracing
        return await super().after_processed(exc_type, exc_val, exc_tb)

    async def on_publish(
            self,
            msg: Any,
            *args: Any,
            **kwargs: Any,
    ) -> Any:
        # Intercept before publish to set correlation_id
        if not isinstance(msg, MsgBaseModel):
            msg = MsgBaseModel(
                data=msg,
            )

        return msg


@before_task_publish.connect
def celery_correlation_id_setter(headers: dict, *_, **__):
    correlation_id = correlation_id_ctx_var.get()
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    headers['x-correlation-id'] = correlation_id


@task_prerun.connect
def celery_correlation_id_getter(task: Task, *_, **__):
    correlation_id = task.request.headers.get('x-correlation-id', '**')
    correlation_id_ctx_var.set(correlation_id)
