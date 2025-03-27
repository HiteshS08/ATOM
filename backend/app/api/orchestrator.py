import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
from app.services.orchestrator import execute_task, get_execution, get_executions

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Define request and response models
class TaskRequest(BaseModel):
    task: str = Field(..., description="The task to be executed")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the task")

class TaskResponse(BaseModel):
    task_id: str = Field(..., description="ID of the task")
    status: str = Field(..., description="Status of the task execution")
    message: str = Field(..., description="Message about the task execution")

class ExecutionStatusResponse(BaseModel):
    task_id: str = Field(..., description="ID of the task")
    original_task: str = Field(..., description="Original task description")
    status: str = Field(..., description="Status of the task execution")
    current_step: int = Field(..., description="Index of the current step")
    steps: List[Dict[str, Any]] = Field(..., description="Steps in the task execution")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Final result of the task execution")
    error: Optional[str] = Field(default=None, description="Error message if task failed")

@router.post("/execute", response_model=TaskResponse)
async def start_task_execution(payload: TaskRequest, background_tasks: BackgroundTasks):
    """
    Start execution of a task
    
    This endpoint takes a task description and starts its execution in the background.
    It returns a task ID that can be used to check the status of the execution.
    """
    if not payload.task:
        logger.error("Task is required but was not provided")
        raise HTTPException(status_code=400, detail="Task description is required")
    
    try:
        # Generate a task ID
        task_id = str(uuid.uuid4())
        
        # Start task execution in the background
        background_tasks.add_task(execute_task, task_id, payload.task)
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Task execution started"
        }
    except Exception as e:
        logger.error(f"Error starting task execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start task execution: {str(e)}")

@router.get("/status/{task_id}", response_model=ExecutionStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a task execution
    
    This endpoint takes a task ID and returns the current status of the task execution.
    """
    execution = get_execution(task_id)
    if not execution:
        logger.error(f"Task execution not found: {task_id}")
        raise HTTPException(status_code=404, detail=f"Task execution not found: {task_id}")
    
    return execution

@router.get("/executions", response_model=Dict[str, ExecutionStatusResponse])
async def list_executions():
    """
    List all task executions
    
    This endpoint returns a list of all task executions.
    """
    return get_executions()