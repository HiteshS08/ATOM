# Multi-Agent Task Orchestration System – Development Plan

This plan outlines how to build a multi-agent task orchestration system from scratch. We’ll proceed in incremental milestones, covering everything from setting up the frontend (React) and backend (FastAPI) to integrating LLMs via Together.ai, implementing a browser automation agent (with Playwright), a code-generation agent, orchestration logic, and finally deploying the system on Render (backend) and Vercel (frontend). Each milestone includes technical details, setup commands, code examples, and testing instructions.

## Architecture Overview

In this architecture, the **Frontend** provides a UI (a simple chat or form) for the user to input a task or query. The **Planner Agent** (powered by an LLM) decomposes the user’s task into smaller subtasks and decides which specialized agent should handle each subtask. We have two main specialist agents: a **Browser Agent** for web interactions (opening pages, clicking, filling forms) and a **Software Engineer (SWE) Agent** for code-related tasks (writing or executing code). An **Orchestrator** component coordinates the execution: it takes the plan from the planner and invokes the appropriate agents (browser or SWE) in sequence or in parallel as needed to perform the subtasks. The system may also include a **Memory** module for storing context (history of tasks, agent outputs) and a toolkit of **Tools** (reusable functions for the agents). The end-to-end flow is: User enters a task → Planner agent plans with LLM → Orchestrator calls Browser/SWE agents to do subtasks → results are aggregated and returned to the frontend for the user.

## Tech Stack and Tools

- **Frontend:** React (JavaScript/TypeScript). We can use Create React App or Next.js for a simple interface. Deployment will be on Vercel (which is well-suited for React apps).

- **Backend:** FastAPI (Python) to expose a REST API that the frontend calls. FastAPI is asynchronous and works well with external I/O (calls to LLM API, browser automation, etc.). We’ll run this on Render as a web service.

- LLM Service:

   Together.ai API to access large language models (e.g., LLaMA-family models). Together.ai provides an easy API to query open-source LLMs (

  Unlocking the World of Large Language Models (LLMs) with Together.ai | by Dr. Ernesto Lee | Medium

  ) (

  Unlocking the World of Large Language Models (LLMs) with Together.ai | by Dr. Ernesto Lee | Medium

  ). We’ll use it for:

  - The Planner Agent (using an instruct model to break down tasks).
  - The SWE Agent’s code generation (using a code-specialized model, e.g., Code LLaMA or similar ([Building an AI data analyst](https://docs.together.ai/docs/data-analyst-agent#:~:text=MODEL_NAME %3D "meta,ai%2Fmodels))).

- **Browser Automation:** Playwright (Python) for driving a real headless browser. Unlike simple web scraping, Playwright controls an actual browser, allowing the agent to interact with web pages like a user – clicking buttons, filling forms, waiting for dynamic content, etc. This is similar to how the Steel Browser API works (Steel is an open-source headless browser for AI agents) ([steel-dev/steel-browser: Open Source Browser API for AI ... - GitHub](https://github.com/steel-dev/steel-browser#:~:text=GitHub github,web without worrying about infrastructure)), but we’ll implement it directly with Playwright.

- **Other Python Libraries:** We’ll use `together` (the official Together.ai SDK for Python), and likely `uvicorn` as an ASGI server to run FastAPI. For development convenience, we’ll also use `fastapi.middleware.cors.CORSMiddleware` to allow the React dev server to call the API (enable CORS).

We will now go through milestones, each adding a layer of functionality.

## Milestone 1: Frontend UI and Basic Backend API

**Objective:** Set up a React frontend with a simple form to accept a task description, and a FastAPI backend with a basic endpoint. Verify that the frontend can send a request to the backend and receive a response. This establishes the end-to-end connection before adding any AI logic.

### Frontend Setup (React)

1. **Initialize React App:** Use Create React App for a quick start. In your terminal:

   ```bash
   npx create-react-app multi-agent-frontend
   cd multi-agent-frontend
   npm start   # start the dev server on http://localhost:3000
   ```

   This creates the project structure and starts a dev server. We’ll later deploy this to Vercel.

2. **Create Input Form:** In the React app (e.g., in `App.js`), create a form or input field where the user can type a task and a button to submit. Use React state to bind the input value and to store the response from the server. For example:

   ```jsx
   // App.js (simplified)
   import { useState } from 'react';
   
   function App() {
     const [task, setTask] = useState("");
     const [result, setResult] = useState("");
   
     const handleSubmit = async (e) => {
       e.preventDefault();
       // Call backend API
       const response = await fetch("http://localhost:8000/execute", {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ task })
       });
       const data = await response.json();
       setResult(data.message);  // assuming backend returns JSON with { "message": ... }
     };
   
     return (
       <div>
         <h1>Multi-Agent Orchestrator</h1>
         <form onSubmit={handleSubmit}>
           <input 
             type="text" 
             value={task} 
             onChange={(e) => setTask(e.target.value)} 
             placeholder="Enter your task..." 
           />
           <button type="submit">Run Task</button>
         </form>
         {result && <div className="result">Result: {result}</div>}
       </div>
     );
   }
   
   export default App;
   ```

   This code captures the user’s task and sends it via a POST request to our backend (assuming it will run at `localhost:8000/execute`). We’ll adjust the URL when deploying (likely using an environment variable for the API base URL). For now, this is fine for local testing.

3. **Styling (Optional):** You can add basic CSS to make the UI clear (e.g., center the form, larger text input). For now, focus on functionality.

### Backend Setup (FastAPI)

1. **Initialize FastAPI Project:** Create a new directory for the backend, e.g., `multi_agent_backend`. Inside, create a virtual environment (optional but recommended) and install FastAPI and Uvicorn:

   ```bash
   cd multi_agent_backend
   python3 -m venv venv
   source venv/bin/activate
   pip install fastapi uvicorn[standard]
   ```

   This installs FastAPI and Uvicorn (an ASGI server to run the app). We will also eventually install `together` and `playwright` when we need them.

2. **Create `main.py`:** This will define our FastAPI app and at least one endpoint. For this milestone, we can create a simple endpoint `/execute` that just echoes back the received task or returns a placeholder message. Also, we should enable CORS so that our React frontend (running on a different origin) can call this API. Example `main.py`:

   ```python
   # main.py
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   
   app = FastAPI()
   
   # Enable CORS for local development (allow calls from localhost:3000)
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],  # Frontend origin
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   
   @app.post("/execute")
   async def execute_task(payload: dict):
       task = payload.get("task", "")
       # For now, just return a simple message. Later, we will integrate the planner and agents here.
       return {"message": f"Received task: {task}"}
   ```

   Here we use `@app.post("/execute")` to define a POST endpoint. We expect a JSON payload with a "task". For now, it simply responds with a confirmation message.

3. **Run the Backend:** Start the FastAPI app with Uvicorn:

   ```bash
   uvicorn main:app --reload --port 8000
   ```

   The app will be running at `http://127.0.0.1:8000`. The `--reload` flag makes it restart on code changes, which is convenient for development.

4. **Test the Connection:** With both frontend (`npm start`) and backend (`uvicorn ...`) running, test the end-to-end flow:

   - Open the React app at `http://localhost:3000`. Enter a sample task (e.g., "Hello World") and submit.
   - The frontend should send the POST request to the backend. You can check the terminal running Uvicorn to see the request log.
   - The backend returns a JSON `{"message": "Received task: Hello World"}`.
   - The frontend then displays this result. Our React code above sets `result` state to the returned message, so you should see something like: **Result: Received task: Hello World** on the page.
   - If you see the correct round-trip, milestone 1 is successful. If not, debug: check browser console for CORS issues (if you forgot to configure CORS or the URL is wrong), check backend logs for errors, etc.

*Milestone 1 provides a basic scaffold: a UI communicating with an API. Next, we’ll implement the intelligent components (LLM planner and agents).*

## Milestone 2: Planner Agent with Together.ai LLM

**Objective:** Implement the Planner Agent logic using an LLM from Together.ai. The planner will take the user’s task and break it into a sequence of subtasks, deciding which agent/tool should handle each subtask. We will integrate the Together.ai API in our FastAPI backend and test that we can get a reasonable plan from a prompt.

### Setting Up Together.ai API Access

1. **Obtain API Key:** Sign up at Together.ai and get an API key (from their dashboard) ([Unlocking the World of Large Language Models (LLMs) with Together.ai | by Dr. Ernesto Lee | Medium](https://ernestodotnet.medium.com/unlocking-the-world-of-large-language-models-llms-with-together-ai-e046a6f78335#:~:text=,your_api_key)). For security, keep this out of code. You can set it as an environment variable, e.g., `TOGETHER_API_KEY`, on your local machine and later in the Render deployment settings.

2. **Install Together SDK:** In the backend environment, install the official Together library:

   ```bash
   pip install together
   ```

   (Version 1.x is expected; at the time of writing `together==1.2.6` is used in their docs ([Building an AI data analyst](https://docs.together.ai/docs/data-analyst-agent#:~:text=Python)).)

3. **Plan Format:** Decide how the planner should output the plan. A simple approach is to have the LLM output JSON or a structured text listing each subtask with an identifier or type. For example, the planner could output a JSON array of subtasks, where each subtask has a `"type"` (e.g., `"browser"` or `"swe"`) and a `"instruction"` describing what to do. We will craft a prompt to encourage this format.

4. **Implement Planner Function:** In `main.py` (or a separate module `planner.py`), write a function that sends the user’s task to the Together.ai LLM and returns the plan. For example:

   ```python
   import os
   from together import Together
   
   # Initialize the Together client (assuming API key is in env variable)
   os.environ["TOGETHER_API_KEY"] = "<YOUR_API_KEY>"  # ideally set this outside code
   client = Together()
   
   PLANNER_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"  # A Together model for instruction following ([Unlocking the World of Large Language Models (LLMs) with Together.ai | by Dr. Ernesto Lee | Medium](https://ernestodotnet.medium.com/unlocking-the-world-of-large-language-models-llms-with-together-ai-e046a6f78335#:~:text=,stream%3DTrue%2C))
   
   def plan_task(user_task: str) -> dict:
       # Define the prompt for the planner LLM
       system_prompt = "You are a planning agent that helps break down tasks for specialized AI agents."
       user_prompt = (
           f"Task: {user_task}\n"
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
       # Call the Together.ai chat completion
       response = client.chat.completions.create(
           model=PLANNER_MODEL,
           messages=messages,
           stream=False
       )
       plan_text = response.choices[0].message.content.strip()
       # Attempt to parse JSON (the model is asked to output JSON)
       import json
       try:
           plan = json.loads(plan_text)
       except json.JSONDecodeError:
           # If parsing fails, return raw text or handle accordingly
           plan = {"steps": plan_text}
       return plan
   ```

   In the above code, we use a smaller Meta LLaMA model (8B instruct) for planning. Together.ai supports many models – you could use larger ones for better quality if needed. We send a conversation with a system prompt (setting the role of the assistant as a planner) and a user prompt containing the task and the instructions. We request a completion (`stream=False` for simplicity, getting the full response at once). The response is expected to be a JSON string describing steps. We then parse it into a Python dict/list. (If the LLM doesn’t strictly output JSON, we handle it gracefully by returning the raw text.)

   **Note:** The model name `"meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"` is one of the Together.ai provided instruct models ([Unlocking the World of Large Language Models (LLMs) with Together.ai | by Dr. Ernesto Lee | Medium](https://ernestodotnet.medium.com/unlocking-the-world-of-large-language-models-llms-with-together-ai-e046a6f78335#:~:text=,stream%3DTrue%2C)). You can choose others; for example, Together has larger LLaMA-2 based models and many open-source models.

5. **Integrate Planner in Endpoint:** Update the FastAPI `/execute` endpoint to use this planner. For now, we might just return the plan (to verify it works). For example:

   ```python
   from fastapi import HTTPException
   
   @app.post("/execute")
   async def execute_task(payload: dict):
       task = payload.get("task", "")
       if not task:
           raise HTTPException(status_code=400, detail="No task provided")
       plan = plan_task(task)  # use the planner function
       return {"plan": plan}
   ```

   This way, when the frontend posts a task, the backend will respond with the plan (either as a structured JSON or as text if parsing failed).

6. **Testing Planner Agent:** Restart the backend (`uvicorn` reloads automatically if running with `--reload`). Use the React frontend or a tool like curl/Postman to test. For example, if you POST `{"task": "Find the latest weather in Paris and write a Python function to convert Celsius to Fahrenheit."}` the planner might respond with a plan, e.g.:

   ```json
   {
     "plan": [
       {"type": "browser", "instruction": "Search for 'latest weather in Paris' and retrieve the information."},
       {"type": "swe", "instruction": "Write a Python function that converts Celsius to Fahrenheit."}
     ]
   }
   ```

   *(The actual output depends on the LLM, but ideally it produces a clear breakdown.)* Verify that you get a sensible breakdown. If the output is not structured as expected, refine the prompt (e.g., emphasize JSON format or adjust the role description). This step ensures the LLM planner is working before moving on.

At this stage, our system can accept a task and use an LLM to generate a plan for subtasks. Next, we implement the specialized agents that will carry out those subtasks.

## Milestone 3: SWE (Software Engineer) Agent with Code Generation

**Objective:** Implement the SWE agent that can handle coding tasks. The SWE agent will likely use an LLM (via Together.ai) specialized in code generation (such as Code LLaMA or other code models ([Building an AI data analyst](https://docs.together.ai/docs/data-analyst-agent#:~:text=MODEL_NAME %3D "meta,ai%2Fmodels))) to write code or solve programming problems. Optionally, it could execute the code to produce results.

### Designing the SWE Agent

1. **Model Selection:** Together.ai provides access to code-optimized models (for example, CodeLlama or StarCoder). We can use a model like `codellama/CodeLlama-13B-Instruct` or one of the Meta LLaMA instruct models with a coding prompt. In Together’s docs, they recommend some models for code generation ([Building an AI data analyst](https://docs.together.ai/docs/data-analyst-agent#:~:text=MODEL_NAME %3D "meta,ai%2Fmodels)) – for example, `codellama/CodeLlama-70b-Instruct-hf` is listed, but that’s very large. For development, a smaller model or instruct model can suffice. We might start with the same model as the planner or a moderately-sized instruct model, and see if it can produce code. If not, switch to a code-specific model.

2. **Implement Code Generation:** Write a function (e.g., `run_swe_agent(subtask)`) that takes a subtask description (instruction) and invokes an LLM to generate code or an answer. For example:

   ```python
   # Assume client = Together() is already initialized as before
   CODE_MODEL = "codellama/CodeLlama-7B-Instruct-hf"  # example code model (if available)
   # Alternatively, use a general instruct model but ask it to provide code.
   
   def run_swe_agent(instruction: str) -> str:
       """Generate code or solution for the given instruction using an LLM."""
       prompt = f"You are a software engineer agent. Task: {instruction}\nProvide the solution in code or appropriate format."
       messages = [{"role": "user", "content": prompt}]
       response = client.chat.completions.create(
           model=CODE_MODEL,
           messages=messages,
           stream=False,
           temperature=0.2  # lower temp for more deterministic output
       )
       result = response.choices[0].message.content
       return result.strip()
   ```

   Here we kept it simple: one user prompt and expecting the assistant to return code. In practice, you might add a system prompt to instruct the model to output only code (or code with explanation). The `temperature=0.2` makes the output more deterministic (less random), since for code we usually want consistent results. Adjust as needed.

3. **(Optional) Execute Code:** Depending on the use-case, the SWE agent might just return code as text, or it might run the code to produce a result (for example, if the task was to compute something or to verify the code works). Executing arbitrary code has security implications, so be careful. In a controlled environment, you could use Python’s `exec()` for Python code or write to a file and run it with subprocess. For this plan, we will not execute arbitrary code by default; we’ll assume the user just wants the code or that running it is safe for known tasks. If needed, one could set up a sandbox or use a service like E2B (Execution to Browser) which Together.ai mentions for code execution ([Building an AI data analyst](https://docs.together.ai/docs/data-analyst-agent#:~:text=In this example%2C we'll show,AI for the LLM piece)) ([Building an AI data analyst](https://docs.together.ai/docs/data-analyst-agent#:~:text=In this example%2C we'll show,AI for the LLM piece)).

4. **Integrate into Orchestration:** We won’t modify the FastAPI endpoint yet to call the SWE agent – that will happen in the orchestration milestone. But we should test the SWE agent function standalone. For example:

   ```python
   print(run_swe_agent("Write a Python function to calculate the factorial of a number."))
   ```

   This should print out Python code for a factorial function. If using an instruct model, you might get some explanation text — if so, refine the prompt (e.g., add "only provide code within markdown block" etc., or use a code-specific model).

5. **Testing the SWE Agent:** You can manually test in a REPL or temporary route. For instance, create a test route in FastAPI:

   ```python
   @app.post("/test_swe")
   async def test_swe(payload: dict):
       instr = payload.get("instruction", "")
       result = run_swe_agent(instr)
       return {"code": result}
   ```

   Then run `uvicorn` and POST a sample instruction to `/test_swe`. Check that you get a plausible code string in the response.

At this point, the SWE agent is ready to generate code for given instructions. We have not yet plugged it into the main flow, but that’s coming. Now, on to the Browser agent.

## Milestone 4: Browser Agent with Real Browser Automation

**Objective:** Implement the Browser Agent using Playwright for Python. This agent will take a web-browsing subtask (e.g., “open this URL and find X” or “search for Y and click result Z”) and execute it in a headless browser, extracting the needed information. We aim to simulate a real user’s browser actions (not just HTTP requests), which is crucial for pages requiring JS execution or interactive login/search.

### Setting Up Playwright

1. **Install Playwright:** In the backend venv, install Playwright:

   ```bash
   pip install playwright
   ```

   After installing the Python package, you need to install browser binaries. Run:

   ```bash
   playwright install
   ```

   This will download Chromium (and Firefox/WebKit if needed) to be used by Playwright ([steel-dev/steel-browser: Open Source Browser API for AI ... - GitHub](https://github.com/steel-dev/steel-browser#:~:text=GitHub github,web without worrying about infrastructure)). (If the backend will be deployed in a container or cloud, ensure this step is done during build or startup. On Render, if using a Dockerfile, you’d run this; if not, you might use their shell to do it once. Alternatively, use the `playwright` Docker base image for convenience.)

2. **Implement Browser Automation:** Create a function for the browser agent, e.g., `run_browser_agent(subtask)`. We can use Playwright’s synchronous API for simplicity here (Playwright also has an async API, which could integrate with FastAPI’s async nature, but using the sync version in a threadpool via FastAPI is fine for now). For example:

   ```python
   from playwright.sync_api import sync_playwright
   
   def run_browser_agent(instruction: str) -> str:
       """
       Execute a browsing task as described by instruction.
       This function opens a browser, performs actions, and returns relevant result (page text, data, etc.).
       """
       result = ""
       # Very basic parsing of instruction to decide action:
       # (In a robust system, the instruction might itself be structured or we need NLP to parse it.
       # For this example, we'll handle a couple of simple known cases.)
       with sync_playwright() as p:
           browser = p.chromium.launch(headless=True)
           page = browser.new_page()
           try:
               if instruction.lower().startswith("open"):
                   # e.g., "Open https://example.com and get the title"
                   # Extract URL
                   words = instruction.split()
                   url = None
                   for word in words:
                       if word.startswith("http"):
                           url = word
                           break
                   if url:
                       page.goto(url)
                   else:
                       # if no URL given, maybe it's a search query:
                       # simplistic approach: if 'search for' in instruction, use a search engine
                       pass
                   # As an example, get page title:
                   result = page.title()
               elif "search for" in instruction.lower():
                   # e.g., "Search for 'Python programming' on Google"
                   query = instruction.split("search for",1)[1]
                   page.goto("https://www.google.com")
                   page.fill("input[name=q]", query)
                   page.keyboard.press("Enter")
                   page.wait_for_timeout(3000)  # wait 3 seconds for results to load
                   result = page.content()  # return the HTML content of results page
               else:
                   # Default: just try to go to the instruction if it looks like a URL
                   if instruction.startswith("http"):
                       page.goto(instruction)
                       result = page.content()
                   else:
                       result = f"Browser agent did not understand instruction: {instruction}"
           finally:
               browser.close()
       return result
   ```

   The above is a simplified example. It demonstrates opening a browser, going to a page or performing a search. In a real scenario, parsing the instruction would be more complex (possibly the planner could output structured directives like `{"action": "open_page", "url": "...", "extract": "title"}` to make it easier). Still, this function shows how to:

   - Launch a headless Chromium browser.
   - Open a new page/tab.
   - Navigate to a URL or perform interactions (filling an input and pressing Enter, etc.).
   - Wait for results (here we just sleep a bit; one could use more specific waits like `page.wait_for_selector` for an element).
   - Extract content (we return the page HTML content or title as the result).
   - Close the browser.

   This is real browser automation: if you run this, it actually opens a browser in memory and can handle dynamic content (for example, if the instruction involved clicking a JavaScript-rendered button, you could do `page.click("selector")` and then extract new content).

3. **Testing the Browser Agent:** Similar to the SWE agent, test this function independently. For example, in `main.py` add a temporary route for debugging:

   ```python
   @app.post("/test_browser")
   def test_browser(payload: dict):
       instr = payload.get("instruction", "")
       result = run_browser_agent(instr)
       # To avoid huge output, maybe just return first 500 chars
       return {"result": result[:500]}
   ```

   Then run a test:

   - POST `{"instruction": "Open https://example.com and get the title"}` to `/test_browser`. You should get back something like `{"result": "Example Domain"}` (or the HTML containing "Example Domain").
   - POST `{"instruction": "Search for Python programming on Google"}`. You should get back HTML content (the Google results page HTML – which will be a lot of content). This confirms the browser agent can perform actions and retrieve data.

   If you encounter errors (for example, Google might detect automation or require a different approach), try using an alternative search engine or ensure headless mode is working. For this development plan, the exact content is not crucial – just that the mechanism works (opening pages, clicking, etc.).

   *Troubleshooting:* If Playwright fails to run due to missing dependencies (especially in Linux server environments), you might need to install system packages (fonts, libcups, etc.). Playwright’s documentation lists dependencies. In a Dockerfile for deployment, using `mcr.microsoft.com/playwright/python` as base image can simplify this, as it comes with dependencies.

Now we have both agents implemented in the backend: the SWE agent (`run_swe_agent`) and the Browser agent (`run_browser_agent`). We can proceed to tie everything together.

## Milestone 5: Orchestrator and Task Execution Flow

**Objective:** Implement the orchestration logic in the backend to use the Planner and agents to fulfill user tasks. The `/execute` endpoint will now orchestrate the following sequence:

1. Use Planner Agent (LLM) to get a task plan (list of subtasks with types).
2. Loop through the plan steps:
   - For each subtask, call the appropriate agent function (`run_browser_agent` or `run_swe_agent`).
   - Collect the results of each step.
   - (Optionally, handle dependencies between steps or pass results from one to another if needed.)
3. Aggregate the results into a final response. This could be as simple as combining text, or could involve an LLM to summarize or format the results.
4. Return the final result to the frontend.

### Implementing the Orchestrator Logic

1. **Update the `/execute` Endpoint:** We will now flesh out the `/execute` function to actually execute the plan. For clarity, let’s break it down inside the function:

   ```python
   @app.post("/execute")
   async def execute_task(payload: dict):
       task = payload.get("task", "")
       if not task:
           raise HTTPException(status_code=400, detail="No task provided")
       # 1. Get plan from Planner Agent
       plan = plan_task(task)
       # If plan is in text form or under a 'steps' key, normalize it to a list
       steps = plan
       if isinstance(plan, dict) and "steps" in plan:
           steps = plan["steps"]
       if isinstance(plan, dict) and "plan" in plan:
           steps = plan["plan"]
       # Ensure steps is a list at this point
       if not isinstance(steps, list):
           # If something went wrong, we cannot proceed
           return {"error": "Planner agent failed to produce a proper plan.", "output": plan}
       
       final_outputs = []  # to store results of each subtask
       # 2. Execute each subtask via appropriate agent
       for step in steps:
           # step could be a dict with 'type' and 'instruction'
           if isinstance(step, dict):
               task_type = step.get("type", "").lower()
               instruction = step.get("instruction") or step.get("task") or ""
           else:
               # if step is not a dict (just a string), decide based on content (not ideal, but fallback)
               instruction = str(step)
               # simple heuristic: if 'code' or 'function' in text, use swe, if 'web' or 'search' use browser
               task_type = "swe" if any(k in instruction.lower() for k in ["code", "function", "script"]) else "browser"
           result = None
           if task_type == "browser":
               result = run_browser_agent(instruction)
           elif task_type == "swe":
               result = run_swe_agent(instruction)
           else:
               # Unknown type: try to handle or skip
               result = f"Unknown task type '{task_type}' for instruction: {instruction}"
           final_outputs.append({"step": instruction, "output": result})
       # 3. (Optional) If we want to use LLM to compile results, we could prompt an LLM here to summarize final_outputs.
       # For simplicity, we'll just return the outputs list.
       return {"results": final_outputs}
   ```

   Let’s break down what this code does:

   - It calls `plan_task(task)` to get the plan.
   - It normalizes the plan into a list of steps (`steps`). Depending on how the LLM responded, we handle if it nested the plan inside a key.
   - It then iterates through each step. Each step ideally is a dict like `{"type": "browser", "instruction": "..."}` from our planner. But we include a fallback if the format is unexpected.
   - For each step, based on the `type`, we call either `run_browser_agent` or `run_swe_agent` with the instruction.
   - We collect the output along with the instruction in `final_outputs`.
   - Finally, we return a JSON with all the step results.
   - (We left a placeholder for optionally summarizing or processing the results. For example, if the task was to "find X and then do Y with it", you might need to pass the result of step1 into step2. A fully smart orchestrator could detect that and modify instructions accordingly. For now, our orchestrator treats steps independently and just returns all their outputs.)

2. **Testing End-to-End (Locally):** Now the big moment: test the entire pipeline locally with an example input.

   - Use the React frontend, or via curl, send a request to `/execute` with a complex task. For example: *“Find the Python website’s title and provide a Python code snippet that prints that title.”*

   - The planner LLM might return something like:

     ```json
     [
       {"type": "browser", "instruction": "Open https://www.python.org and get the page title."},
       {"type": "swe", "instruction": "Print the title obtained in the previous step using a Python print statement."}
     ]
     ```

   - The orchestrator will then:

     - Call `run_browser_agent("Open https://www.python.org and get the page title.")` – this will open the page and return the title text (e.g., "Welcome to Python.org").

     - Call `run_swe_agent("Print the title obtained in the previous step using a Python print statement.")`. Our SWE agent doesn’t know the actual title (since we didn’t pipe it in), so this is a limitation in this simplistic approach. It might just produce something like `print("Welcome to Python.org")` as code, but it won’t truly know the title unless the planner or orchestrator fed it. In a more advanced design, the orchestrator could replace placeholders in the second instruction with results from the first (the planner could output a variable reference). For now, assume independent tasks or that the LLM might include the data if it planned it explicitly.

     - The final result returned would be a JSON with both steps and their outputs. Something like:

       ```json
       {
         "results": [
           {
             "step": "Open https://www.python.org and get the page title.",
             "output": "Welcome to Python.org"
           },
           {
             "step": "Print the title obtained in the previous step using a Python print statement.",
             "output": "```python\nprint(\"Welcome to Python.org\")\n```"
           }
         ]
       }
       ```

   - The React frontend can then display these results in a user-friendly way. For example, you might update the UI to format each step’s output nicely (if code, show in a code block; if text, just show text).

   Test with a few different tasks:

   - Pure browsing task: “Find the top headline on CNN.com”. (Planner likely one browser step; Browser agent should return a chunk of HTML or text containing the headline – you might refine the agent to specifically return, say, the text of `<h1>`.)
   - Pure coding task: “Write a Python function to check if a number is prime.” (Planner likely one SWE step; SWE agent should return code.)
   - Mixed task like the Python title example above, or “Search for the GitHub repository with most stars about machine learning and generate a shell command to clone it.” (Just to push the capabilities – the planner might say browser to search GitHub, and swe to produce `git clone ...` command.)

   Debug and tweak as needed. Pay attention to error handling: if the planner fails or an agent errors out (exception in browser agent, etc.), ensure the `/execute` returns an error message instead of crashing. You can wrap agent calls in try/except and return a partial result with an error note if something fails.

By the end of Milestone 5, we have a functioning system locally: the user enters a task, the backend plans and executes it with two agents, and returns results. The frontend displays the results. The core logic is in place.

## Milestone 6: Deployment on Render and Vercel

**Objective:** Deploy the backend to Render and the frontend to Vercel, so the system is accessible to users via a web UI. We’ll package the code, push to GitHub, and use cloud deployment platforms.

### Preparing for Deployment

- Repository Setup:

   Create two separate Git repositories (or two directories in one mono-repo, though separate repos might be simpler):

  - `multi-agent-backend` for the FastAPI app.
  - `multi-agent-frontend` for the React app.

- Ensure all necessary files are in place:

  - Backend:

    ```
    main.py
    ```

    , requirements.txt (list FastAPI, uvicorn, together, playwright, etc.), and possibly a 

    ```
    Dockerfile
    ```

     or 

    ```
    render.yaml
    ```

     if needed.

    - A simple 

      ```
      requirements.txt
      ```

       example:

      ```
      fastapi
      uvicorn[standard]
      together
      playwright
      ```

    - If not using Docker, include a note in `README.md` that after install one should run `playwright install`. On Render, we can handle that as described below.

  - **Frontend:** If using Create React App, ensure the project has the usual `package.json`, etc. After development, run `npm run build` to generate a production build (the `build` directory). For Vercel, you can deploy directly from source; Vercel will run the build command automatically.

### Deploying the Backend on Render

1. **Create a Web Service on Render:** Log in to Render.com and choose “New > Web Service”. Connect it to your GitHub repo (multi-agent-backend). Render will detect it’s a Python app (due to requirements or a Procfile).

2. **Specify Start Command:** In the Render settings for this service, set the start command to:
    `uvicorn main:app --host 0.0.0.0 --port $PORT`
    This is the command Render will use to run the FastAPI app on their platform (the `$PORT` env is provided by Render) ([GitHub - render-examples/fastapi: Template to deploy a simple Python FastAPI project to Render](https://github.com/render-examples/fastapi#:~:text=5,the Start Command)) ([GitHub - render-examples/fastapi: Template to deploy a simple Python FastAPI project to Render](https://github.com/render-examples/fastapi#:~:text=uvicorn main%3Aapp ,PORT)).

3. **Environment Variables:** Add your Together AI API key in Render’s “Environment Variables” section as `TOGETHER_API_KEY`. Also, if Playwright or other tools need any environment config, add those. (Often not needed, but just in case.)

4. **Playwright on Render:** Since we rely on Playwright, which needs a headless browser, we need to ensure the deployment has the browsers. Two approaches:

   - Use Render’s Docker deployment: Write a 

     ```
     Dockerfile
     ```

      that installs Python packages and runs 

     ```
     playwright install
     ```

     . For example:

     ```dockerfile
     FROM python:3.10-slim
     WORKDIR /app
     COPY requirements.txt .
     RUN pip install -r requirements.txt
     # Install playwright browsers
     RUN playwright install --with-deps chromium
     COPY . .
     CMD uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

     Then in Render, enable “Deploy from Dockerfile”. This ensures Chromium is set up.

   - Or, use Render’s native environment: Render’s Python environment might not automatically have Chromium. You could try adding a 

     ```
     post-build
     ```

      step in a 

     ```
     render.yaml
     ```

      to run 

     ```
     playwright install
     ```

     . Example 

     ```
     render.yaml
     ```

     :

     ```yaml
     services:
       - type: web
         name: multi-agent-backend
         env: python
         buildCommand: pip install -r requirements.txt && playwright install chromium
         startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

     This YAML can be committed to your repo so Render knows how to build and run. (Or configure equivalent in the web dashboard.)

   - Verify in Render’s logs that the app starts successfully and Playwright can launch a browser. (Render might require the `--no-sandbox` flag for Chromium; if so, modify launch: `browser = p.chromium.launch(headless=True, args=["--no-sandbox"])`.)

5. **Test Backend API (Post-deploy):** Once deployed, Render will give a public URL (something like `https://multi-agent-backend.onrender.com`). Test this with a tool like curl:

   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"task": "write 1+1 in python"}' https://multi-agent-backend.onrender.com/execute
   ```

   You should get a JSON response with the plan and result. If this works, backend is live.

### Deploying the Frontend on Vercel

1. **Create Vercel Project:** Log in to Vercel.com and create a new project, selecting your `multi-agent-frontend` repository. Vercel will autodetect a React app (if it was created with CRA or Next.js).

2. **Configure Build:** Ensure the project’s settings on Vercel have the correct build command (`npm run build`) and publish directory (`build/` for CRA). This is usually auto-set.

3. **Environment Variable for API URL:** If your frontend code calls `http://localhost:8000/execute`, you need to change that to the Render URL. **Do not** hardcode the Render URL in code, because in development you used localhost. Instead, use an environment variable. For CRA, you can use `REACT_APP_API_URL`. For example, update the fetch call:

   ```jsx
   const response = await fetch(`${process.env.REACT_APP_API_URL}/execute`, { ... });
   ```

   In development, you can set this in a `.env` file as `REACT_APP_API_URL=http://localhost:8000`. In production (Vercel), set an Environment Variable `REACT_APP_API_URL` to `https://multi-agent-backend.onrender.com` (your actual backend URL). Vercel will embed that at build time.

4. **Deploy:** Once configured, trigger a deploy on Vercel (it might auto-deploy on pushing to main branch). Wait for the build to complete and verify the frontend is live (you’ll get a domain, e.g., `https://multi-agent-frontend.vercel.app`).

5. **Test the Live System:** Visit the Vercel URL in your browser. Try inputting tasks as before. The frontend will make requests to the Render backend and display results. Monitor the backend logs on Render for any runtime errors (especially for Playwright actions or LLM calls). Also check the network calls in the browser dev tools to ensure the requests are going through and responses are received. Example:

   - Enter: “What’s the latest news on Tesla, and generate Python code to calculate 2+2.”
   - Planner might split into two steps: Browser agent searches news on Tesla, SWE agent returns `print(2+2)` or `4`.
   - The frontend should show perhaps a large chunk (news text) and the code. This shows the system working end-to-end in production.

### Final Touches and Considerations

- **Error Handling & Timeouts:** In production, you might want to add timeouts to LLM calls or browser actions to avoid hanging if something goes wrong. FastAPI and httpx (used by Together SDK) can allow timeouts. Playwright calls can also have timeouts or you can set a maximum runtime for each step.
- **Security:** Make sure the backend is not open to misuse. Right now, it allows running an arbitrary browser and possibly code – in a public system, that could be abused. Implement rate limiting or authentication for the API if needed, and consider restricting what the SWE agent can do (maybe disable actual code execution unless necessary).
- **Improving Planner and Agents:** The basic planner might produce imperfect plans. In the future, you could fine-tune it or implement a feedback loop (agents reporting success/failure to a controller which can re-plan). The agents themselves could be more sophisticated (the browser agent could parse specific info instead of dumping HTML, etc.).
- **Memory Module:** The architecture diagram (above) included a memory component. In our implementation, we did not add long-term memory, but you could store past interactions or results (e.g., in a database or in-memory structure) and feed them into the planner as context for subsequent requests (if the system needs conversational continuity or learning from past tasks).
- **Logging and Monitoring:** It’s useful to log each step (on the backend) – e.g., log the plan and each agent’s result – for debugging. On Render, you can view logs. In a real app, you might integrate with a logging service.
- **Testing:** Write unit tests for `plan_task`, `run_swe_agent`, and `run_browser_agent` functions with sample inputs. Since they depend on external services, you might mock the LLM responses or run them with known outputs for consistency. Integration testing can be done by running the FastAPI app locally and hitting the endpoints with various payloads to ensure the responses are as expected.

## Conclusion

By following these milestones, you will incrementally build a multi-agent orchestration system:

- A user-friendly React frontend for input and output.
- A robust FastAPI backend orchestrating between an LLM-based planner, a code-generating agent, and a real browser-automation agent.
- Integration with Together.ai’s APIs for AI capabilities (planning and coding).
- Real web interaction through Playwright, analogous to how a human or a tool like Steel Browser would control a browser.
- Deployment instructions to host the service (FastAPI on Render with proper setup for headless browsing, React on Vercel for scalability and ease of access).

By the end, the deployed system will allow a user to enter a high-level task and get results after the system intelligently breaks it down and executes each part. For example, entering *“Find the first paragraph of Wikipedia’s article on FastAPI and generate Python code to make an HTTP GET request to that site”* would trigger the browser agent to fetch that paragraph and the SWE agent to produce the code, returning both results to the user. Each milestone built towards this capability, ensuring that at every step, the components were tested and functional before integrating the next piece.