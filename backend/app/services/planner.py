import os
import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from together import Together
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Together client
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# Model configuration - using confirmed free models from Together.ai
PRIMARY_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
FALLBACK_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"

# Define data models for better type safety and validation
class SubTask(BaseModel):
    """Model representing a subtask in the plan"""
    type: str = Field(..., description="Type of agent to handle this task (browser or swe)")
    instruction: str = Field(..., description="Detailed instruction for the agent")
    dependencies: Optional[List[int]] = Field(default=None, description="List of step indices this task depends on")
    
class TaskPlan(BaseModel):
    """Model representing the complete task plan"""
    steps: List[SubTask] = Field(..., description="List of subtasks to execute")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the plan")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((json.JSONDecodeError, KeyError, Exception)),
    reraise=True
)
def plan_task(task: str) -> dict:
    """
    Create a detailed execution plan for a given task using LLM.
    
    Args:
        task: The user's task description
        
    Returns:
        A dictionary containing the plan with steps and context
    """
    logger.info(f"Planning task: {task}")
    
    # Enhanced system prompt with more detailed instructions
    system_prompt = """You are an advanced planning agent that breaks down complex tasks into executable subtasks.
Your role is to analyze the user's request and create a detailed, structured plan that specialized AI agents can follow.
You must think carefully about dependencies between tasks and ensure the plan is comprehensive and logical.
"""

    # Enhanced user prompt with more detailed instructions and examples
    user_prompt = f"""Task: {task}

Break this task into a detailed list of subtasks. For each subtask:
1. Determine which specialized agent should handle it:
   - browser: For web browsing, search, form-filling, clicking, scrolling, or any web interaction tasks
   - swe: For coding, computation, file operations, or any software engineering tasks

2. Write clear, specific instructions for each subtask
3. Consider dependencies between subtasks (which steps must complete before others can begin)

Provide your plan as a valid JSON object with the following structure:
{{
  "steps": [
    {{
      "type": "browser|swe",
      "instruction": "Detailed instruction for the agent",
      "dependencies": [list of step indices this task depends on, or null if no dependencies]
    }}
  ],
  "context": {{
    "additional_info": "Any relevant context that might help with execution"
  }}
}}

Ensure your JSON is valid and properly formatted. Each instruction should be detailed enough for an agent to execute without additional clarification.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        # Try with primary model
        logger.info(f"Generating plan with model: {PRIMARY_MODEL}")
        response = client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=messages,
            stream=False,
            temperature=0.2,  # Lower temperature for more deterministic planning
            max_tokens=2048
        )
        plan_text = response.choices[0].message.content
        
    except Exception as e:
        # Fallback to secondary model if primary fails
        logger.warning(f"Primary model failed: {str(e)}. Falling back to {FALLBACK_MODEL}")
        response = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=messages,
            stream=False,
            temperature=0.2,
            max_tokens=2048
        )
        plan_text = response.choices[0].message.content
    
    # Clean up the response text
    if "<think>" in plan_text and "</think>" in plan_text:
        think_start = plan_text.find("<think>")
        think_end = plan_text.find("</think>") + len("</think>")
        clean_text = plan_text[think_end:].strip()
    else:
        clean_text = plan_text
    
    # Extract JSON from markdown code blocks if present
    if "```json" in clean_text and "```" in clean_text:
        start = clean_text.find("```json") + len("```json")
        end = clean_text.rfind("```")
        clean_text = clean_text[start:end].strip()
    elif "```" in clean_text and "```" in clean_text[clean_text.find("```")+3:]:
        start = clean_text.find("```") + len("```")
        end = clean_text.rfind("```")
        clean_text = clean_text[start:end].strip()
    
    try:
        # Parse the JSON response
        plan_dict = json.loads(clean_text)
        
        # Validate with Pydantic model
        if "steps" in plan_dict:
            plan = TaskPlan(**plan_dict)
            logger.info(f"Successfully created plan with {len(plan.steps)} steps")
            return plan.model_dump()
        else:
            # Handle case where JSON is valid but doesn't match our expected structure
            logger.warning("JSON response missing 'steps' key, returning as-is")
            return {"steps": [{"type": "swe", "instruction": "Review and fix the plan structure", "dependencies": None}],
                    "context": {"original_response": plan_dict}}
            
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors with a structured error response
        logger.error(f"Failed to parse JSON: {str(e)}")
        return {
            "steps": [
                {"type": "swe", "instruction": "Parse and structure the following plan", "dependencies": None}
            ],
            "context": {
                "error": "JSON parsing failed",
                "original_text": clean_text
            }
        }
