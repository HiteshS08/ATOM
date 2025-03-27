import os
import json
import logging
import asyncio
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
SWE_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
FALLBACK_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"

class CodeResult(BaseModel):
    """Model representing the result of a code generation task"""
    code: str = Field(..., description="The generated code")
    language: str = Field(..., description="The programming language of the code")
    explanation: Optional[str] = Field(default=None, description="Explanation of the code")
    
class SWEResult(BaseModel):
    """Model representing the result of a SWE agent execution"""
    success: bool = Field(..., description="Whether the execution was successful")
    result: Optional[CodeResult] = Field(default=None, description="The result of the execution")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((json.JSONDecodeError, KeyError, Exception)),
    reraise=True
)
async def run_swe_agent(instruction: str) -> Dict[str, Any]:
    """
    Generate code or solution for the given instruction using an LLM.
    
    Args:
        instruction: The instruction for the SWE agent
        
    Returns:
        A dictionary containing the execution results
    """
    logger.info(f"Running SWE agent with instruction: {instruction}")
    
    # Enhanced system prompt with more detailed instructions
    system_prompt = """You are an expert software engineer with deep knowledge of programming languages, 
frameworks, and best practices. Your task is to write high-quality, efficient, and well-documented code 
based on the user's requirements.

Guidelines:
- Write clean, readable, and maintainable code
- Include appropriate error handling
- Follow best practices for the specific language/framework
- Provide clear comments explaining complex logic
- Consider edge cases and potential issues
- Optimize for performance and efficiency where appropriate
- Include imports/dependencies as needed

Your response should be structured as follows:
1. The complete code solution in a code block
2. A brief explanation of how the code works
3. Any assumptions or limitations of your implementation
"""

    # Prepare the user prompt
    user_prompt = f"Task: {instruction}\n\nPlease provide a complete solution for this task."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        # Try with primary model
        logger.info(f"Generating code with model: {SWE_MODEL}")
        response = client.chat.completions.create(
            model=SWE_MODEL,
            messages=messages,
            stream=False,
            temperature=0.2,  # Lower temperature for more deterministic code generation
            max_tokens=4096
        )
        result_text = response.choices[0].message.content
        
    except Exception as e:
        # Fallback to secondary model if primary fails
        logger.warning(f"Primary model failed: {str(e)}. Falling back to {FALLBACK_MODEL}")
        response = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=messages,
            stream=False,
            temperature=0.2,
            max_tokens=4096
        )
        result_text = response.choices[0].message.content
    
    # Process the response to extract code and explanation
    try:
        # Extract code blocks
        code_blocks = []
        explanation = result_text
        
        # Find all code blocks (```language ... ```)
        import re
        code_block_pattern = r"```(\w*)\n([\s\S]*?)```"
        matches = re.findall(code_block_pattern, result_text)
        
        if matches:
            # Extract the first code block (language, code)
            language, code = matches[0]
            if not language:
                language = "text"  # Default if language not specified
                
            # Remove code blocks from explanation
            explanation = re.sub(code_block_pattern, "", result_text).strip()
            
            # Create result
            code_result = CodeResult(
                code=code.strip(),
                language=language,
                explanation=explanation
            )
            
            return SWEResult(
                success=True,
                result=code_result
            ).dict()
        else:
            # No code blocks found, treat the entire response as code
            # Try to guess the language based on content
            language = "text"
            if "def " in result_text and (":" in result_text or "import " in result_text):
                language = "python"
            elif "function " in result_text and ("{" in result_text or "=>" in result_text):
                language = "javascript"
            elif "public class " in result_text or "import java." in result_text:
                language = "java"
            
            return SWEResult(
                success=True,
                result=CodeResult(
                    code=result_text,
                    language=language,
                    explanation="No separate explanation provided."
                )
            ).dict()
            
    except Exception as e:
        logger.error(f"Error processing SWE agent result: {str(e)}")
        return SWEResult(
            success=False,
            error=f"Failed to process result: {str(e)}"
        ).dict()