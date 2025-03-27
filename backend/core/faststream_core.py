"""
Core functionality for FastStream message processing and logging.

This module provides base models, message status tracking, and logging utilities
for FastStream applications. It includes correlation ID tracking to help trace
message flow through the system.
"""
import asyncio
import logging
import uuid
from enum import Enum
from functools import wraps
from typing import Optional, Generic, TypeVar

from pydantic import BaseModel, Field

from .context_var import correlation_id_ctx_var

T = TypeVar('T')


class MsgBaseModel(BaseModel, Generic[T]):
    """
    Base model for all FastStream messages.
    
    Attributes:
        correlation_id: Unique identifier to track message through the system
        data: Optional payload of type T carried by the message
    """
    correlation_id: str = Field(init=False, default_factory=lambda: correlation_id_ctx_var.get() or str(uuid.uuid4()))
    data: Optional[T] = None


class MessageStatus(str, Enum):
    """
    Enum representing possible states of a message in the system.
    
    States:
        RECEIVED: Message has been received by the system
        PROCESSING: Message is currently being processed
        COMPLETED: Message processing completed successfully
        FAILED: Message processing failed
        RETRYING: System is retrying message processing
        CANCELLED: Message processing was cancelled
        PARTIALLY: Message was partially processed
    """
    RECEIVED = "Received"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    RETRYING = "Retrying"
    CANCELLED = "Cancelled"
    PARTIALLY = "Partially"


def create_record_factory(original_factory, correlation_id):
    """
    Creates a custom log record factory that adds correlation ID to log messages.
    
    Args:
        original_factory: Original logging record factory
        correlation_id: Correlation ID to be added to log messages
        
    Returns:
        Function that creates log records with correlation ID prefix
    """

    def record_factory(*record_args, **record_kwargs):
        record = original_factory(*record_args, **record_kwargs)
        record.msg = f"[ {correlation_id} ] - {record.msg}"
        return record

    return record_factory


def log_faststream(func):
    """
    Decorator that adds correlation ID context to log messages.
    
    This decorator extracts correlation_id from function arguments and adds it
    to all log messages generated during function execution. Supports both
    synchronous and asynchronous functions.
    
    Args:
        func: Function to be decorated
        
    Returns:
        Wrapped function that includes correlation ID in its log messages
    """

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        original_factory = logging.getLogRecordFactory()
        correlation_id = next(
            (
                getattr(arg, 'correlation_id', None)
                for arg in list(args) + list(kwargs.values())
                if hasattr(arg, 'correlation_id')
            ),
            '**'
        )

        logging.setLogRecordFactory(create_record_factory(original_factory, correlation_id))
        try:
            return func(*args, **kwargs)
        finally:
            logging.setLogRecordFactory(original_factory)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        original_factory = logging.getLogRecordFactory()
        correlation_id = next(
            (
                getattr(arg, 'correlation_id', None)
                for arg in list(args) + list(kwargs.values())
                if hasattr(arg, 'correlation_id')
            ),
            '**'
        )

        logging.setLogRecordFactory(create_record_factory(original_factory, correlation_id))
        try:
            return await func(*args, **kwargs)
        finally:
            logging.setLogRecordFactory(original_factory)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
