import os
from together import Together
from dotenv import load_dotenv
import json
load_dotenv()

client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

PLANNER_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"

def plan_task(task: str) -> dict:
    system_prompt = "You are a planning agent that helps break down tasks for specialized AI agents."
    user_prompt = (
        f"Task: {task}\n"
        "Break this task into a list of subtasks. "
        "Decide which of the following agents is best for each subtask:\n"
        "- browser: for web browsing, search, or form-filling tasks.\n"
        "- swe: for coding or computation tasks.\n"
        "Provide the plan as a JSON list of steps, where each step has 'type' and 'instruction'."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    response = client.chat.completions.create(
        model=PLANNER_MODEL,
        messages=messages,
        stream=False
    )
    plan_text = response.choices[0].message.content
    if "<think>" in plan_text and "</think>" in plan_text:
        think_start = plan_text.find("<think>")
        think_end = plan_text.find("</think>") + len("</think>")
        clean_text = plan_text[think_end:].strip()
    else:
        clean_text = plan_text
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        return {"plan": clean_text}
