import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from app.services.planner import plan_task
from app.services.browser_agent import run_browser_task
from app.services.swe_agent import run_swe_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStep(BaseModel):
    """Model representing a step in the task execution"""
    step_index: int = Field(..., description="Index of the step")
    type: str = Field(..., description="Type of agent used (browser or swe)")
    instruction: str = Field(..., description="Instruction for the agent")
    status: str = Field(default="pending", description="Status of the step (pending, running, completed, failed)")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Result of the step execution")
    error: Optional[str] = Field(default=None, description="Error message if step failed")
    
class TaskExecution(BaseModel):
    """Model representing the execution of a task"""
    task_id: str = Field(..., description="ID of the task")
    original_task: str = Field(..., description="Original task description")
    status: str = Field(default="pending", description="Status of the task execution")
    steps: List[TaskStep] = Field(default_factory=list, description="Steps in the task execution")
    current_step: int = Field(default=0, description="Index of the current step")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Final result of the task execution")
    error: Optional[str] = Field(default=None, description="Error message if task failed")

class Orchestrator:
    """Orchestrator that coordinates between the planner, browser agent, and SWE agent"""
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.executions = {}
        
    async def _execute_step(self, execution: TaskExecution, step: TaskStep) -> Dict[str, Any]:
        """
        Execute a single step in the task execution
        
        Args:
            execution: The task execution
            step: The step to execute
            
        Returns:
            The result of the step execution
        """
        logger.info(f"Executing step {step.step_index} of type {step.type} for task {execution.task_id}")
        
        # Update step status
        step.status = "running"
        
        try:
            # Execute step based on type
            if step.type.lower() == "browser":
                result = await run_browser_task(step.instruction)
            elif step.type.lower() == "swe":
                result = await run_swe_agent(step.instruction)
            else:
                raise ValueError(f"Unknown step type: {step.type}")
            
            # Update step with result
            step.status = "completed"
            step.result = result
            return result
        except Exception as e:
            logger.error(f"Error executing step {step.step_index}: {str(e)}")
            step.status = "failed"
            step.error = str(e)
            raise
    
    async def execute_task(self, task_id: str, task: str) -> TaskExecution:
        """
        Execute a task using the planner, browser agent, and SWE agent
        
        Args:
            task_id: ID of the task
            task: The task to execute
            
        Returns:
            The task execution
        """
        logger.info(f"Executing task {task_id}: {task}")
        
        # Create task execution
        execution = TaskExecution(
            task_id=task_id,
            original_task=task,
            status="planning"
        )
        self.executions[task_id] = execution
        
        try:
            # Plan the task
            plan = plan_task(task)
            
            # Create steps from plan
            steps = []
            for i, step_data in enumerate(plan.get("steps", [])):
                step = TaskStep(
                    step_index=i,
                    type=step_data.get("type", "unknown"),
                    instruction=step_data.get("instruction", "")
                )
                steps.append(step)
            
            execution.steps = steps
            execution.status = "executing"
            
            # Execute steps
            for i, step in enumerate(steps):
                execution.current_step = i
                
                # Check if step has dependencies
                dependencies = step_data.get("dependencies", [])
                if dependencies:
                    # Check if all dependencies are completed
                    for dep_index in dependencies:
                        if dep_index >= 0 and dep_index < len(steps):
                            dep_step = steps[dep_index]
                            if dep_step.status != "completed":
                                logger.warning(f"Dependency {dep_index} not completed for step {i}")
                                step.status = "failed"
                                step.error = f"Dependency {dep_index} not completed"
                                execution.status = "failed"
                                execution.error = f"Step {i} failed: Dependency {dep_index} not completed"
                                return execution
                
                # Execute step
                try:
                    await self._execute_step(execution, step)
                except Exception as e:
                    execution.status = "failed"
                    execution.error = f"Step {i} failed: {str(e)}"
                    return execution
            
            # All steps completed successfully
            execution.status = "completed"
            execution.result = {
                "steps": [step.dict() for step in steps]
            }
            return execution
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}")
            execution.status = "failed"
            execution.error = str(e)
            return execution
    
    def get_execution(self, task_id: str) -> Optional[TaskExecution]:
        """
        Get a task execution by ID
        
        Args:
            task_id: ID of the task
            
        Returns:
            The task execution, or None if not found
        """
        return self.executions.get(task_id)
    
    def get_executions(self) -> Dict[str, TaskExecution]:
        """
        Get all task executions
        
        Returns:
            Dictionary of task executions
        """
        return self.executions

# Create a singleton instance
orchestrator = Orchestrator()

async def execute_task(task_id: str, task: str) -> Dict[str, Any]:
    """
    Execute a task using the orchestrator
    
    Args:
        task_id: ID of the task
        task: The task to execute
        
    Returns:
        The task execution as a dictionary
    """
    execution = await orchestrator.execute_task(task_id, task)
    return execution.dict()

def get_execution(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a task execution by ID
    
    Args:
        task_id: ID of the task
        
    Returns:
        The task execution as a dictionary, or None if not found
    """
    execution = orchestrator.get_execution(task_id)
    return execution.dict() if execution else None

def get_executions() -> Dict[str, Dict[str, Any]]:
    """
    Get all task executions
    
    Returns:
        Dictionary of task executions as dictionaries
    """
    return {task_id: execution.dict() for task_id, execution in orchestrator.get_executions().items()}