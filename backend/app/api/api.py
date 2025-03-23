from fastapi import APIRouter, HTTPException
from app.services.planner import plan_task as planner_task
router = APIRouter()

@router.post("/plan")
async def plan_task(payload: dict):
    task_plan = payload.get("task_plan")
    if not task_plan:
        raise HTTPException(status_code=400, detail="Task plan is required")
    plan = planner_task(task_plan)
    return plan
