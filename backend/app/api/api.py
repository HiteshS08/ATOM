from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from app.services.planner import plan_task as planner_task

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Define request and response models for better API documentation and validation
class TaskRequest(BaseModel):
    task: str = Field(..., description="The task to be planned and executed")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the task")

class SubTask(BaseModel):
    type: str = Field(..., description="Type of agent to handle this task (browser or swe)")
    instruction: str = Field(..., description="Detailed instruction for the agent")
    dependencies: Optional[List[int]] = Field(default=None, description="List of step indices this task depends on")

class TaskPlanResponse(BaseModel):
    steps: List[SubTask] = Field(..., description="List of subtasks to execute")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the plan")

@router.post("/plan", response_model=TaskPlanResponse)
async def plan_task(payload: TaskRequest, background_tasks: BackgroundTasks):
    """
    Create a detailed execution plan for a given task.
    
    This endpoint takes a task description and returns a structured plan with steps
    for different specialized agents to execute.
    """
    if not payload.task:
        logger.error("Task plan is required but was not provided")
        raise HTTPException(status_code=400, detail="Task description is required")
    
    try:
        logger.info(f"Planning task: {payload.task[:50]}...")
        plan = planner_task(payload.task)
        return plan
    except Exception as e:
        logger.error(f"Error planning task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to plan task: {str(e)}")
