import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from pydantic import BaseModel, Field
from browser_use import Agent, BrowserConfig, SystemPrompt
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
BROWSER_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
FALLBACK_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"

class BrowserStep(BaseModel):
    """Model representing a step in the browser agent's execution"""
    action: str = Field(..., description="The action performed")
    screenshot: Optional[str] = Field(default=None, description="Base64 encoded screenshot")
    result: Optional[str] = Field(default=None, description="Result of the action")
    error: Optional[str] = Field(default=None, description="Error message if action failed")

class BrowserResult(BaseModel):
    """Model representing the result of a browser agent execution"""
    success: bool = Field(..., description="Whether the execution was successful")
    steps: List[BrowserStep] = Field(default_factory=list, description="List of steps executed")
    final_result: Optional[str] = Field(default=None, description="Final result of the execution")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")

class CustomSystemPrompt(SystemPrompt):
    """Custom system prompt for the browser agent with enhanced instructions"""
    
    def get_content(self) -> str:
        """Return the system prompt content"""
        return """You are an expert browser automation agent that can perform tasks in a web browser.
Your goal is to complete the user's task by interacting with web pages through a browser.

You have access to the following actions:
1. navigate(url): Navigate to a specific URL
2. click(selector): Click on an element matching the selector
3. type(selector, text): Type text into an element matching the selector
4. extract(selector): Extract text from elements matching the selector
5. scroll(direction): Scroll the page (up, down, left, right)
6. wait(milliseconds): Wait for a specified time in milliseconds
7. screenshot(): Take a screenshot of the current page

Guidelines:
- Be precise with your selectors (use CSS selectors or XPath)
- Break complex tasks into simple steps
- Handle errors gracefully and try alternative approaches when needed
- Provide clear explanations of what you're doing
- When extracting information, be specific about what you're looking for
- Always verify that pages have loaded before interacting with them

Remember that you are interacting with real web pages, so be patient and handle dynamic content appropriately.
"""

class BrowserAgent:
    """Browser agent that can execute tasks in a web browser using BrowserUse"""
    
    def __init__(self):
        """Initialize the browser agent"""
        self.steps = []
        self.current_step = 0
        
    async def _step_callback(self, step_index: int, step_data: Dict[str, Any]) -> None:
        """Callback function for each step in the browser agent's execution"""
        logger.info(f"Step {step_index}: {step_data.get('action', 'Unknown action')}")
        
        # Create a step record
        step = BrowserStep(
            action=step_data.get("action", "Unknown action"),
            screenshot=step_data.get("screenshot"),
            result=step_data.get("result"),
            error=step_data.get("error")
        )
        
        # Add to steps list
        self.steps.append(step)
        self.current_step = step_index
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def execute_task(self, task: str) -> BrowserResult:
        """
        Execute a task in a web browser
        
        Args:
            task: The task to execute
            
        Returns:
            A BrowserResult object containing the execution results
        """
        logger.info(f"Executing browser task: {task}")
        self.steps = []
        self.current_step = 0
        
        try:
            # Create LLM for the agent
            llm = {
                "provider": "together",
                "config": {
                    "model": BROWSER_MODEL,
                    "api_key": os.getenv("TOGETHER_API_KEY"),
                    "temperature": 0.2
                }
            }
            
            # Create browser configuration
            browser_config = BrowserConfig(
                headless=True,
                viewport_width=1280,
                viewport_height=720,
                locale="en-US",
                timezone_id="America/New_York",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
            )
            
            # Create and run the agent
            agent = Agent(
                task=task,
                llm=llm,
                browser_config=browser_config,  # Updated parameter name
                register_new_step_callback=self._step_callback,
                system_prompt_class=CustomSystemPrompt
            )
            
            # Execute the task
            result = await agent.run()
            
            # Create and return the result
            return BrowserResult(
                success=True,
                steps=self.steps,
                final_result=result
            )
            
        except Exception as e:
            logger.error(f"Error executing browser task: {str(e)}")
            return BrowserResult(
                success=False,
                steps=self.steps,
                error=str(e)
            )
        finally:
            # No need to explicitly close browser context in newer versions
            # The Agent class handles this automatically
            pass

# Create a singleton instance
browser_agent = BrowserAgent()

async def run_browser_task(task: str) -> Dict[str, Any]:
    """
    Run a task in the browser agent
    
    Args:
        task: The task to execute
        
    Returns:
        A dictionary containing the execution results
    """
    result = await browser_agent.execute_task(task)
    return result.dict()