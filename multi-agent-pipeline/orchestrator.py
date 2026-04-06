import os
from typing import TypedDict, Annotated, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import json
from workers import get_worker, list_workers

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

if os.getenv("LANGSMITH_API_KEY"):
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "multi-agent-pipeline")

class SubTask(TypedDict):
    worker: str
    task: str
    reasoning: str

class AgentState(TypedDict):
    task: str
    subtasks: list[SubTask]
    worker_results: list[dict]
    final_output: str

def decompose_task(state: AgentState) -> AgentState:
    """Decompose complex task into subtasks with worker assignments."""
    task = state["task"]
    available_workers = list_workers()
    
    system_instruction = f"""You are an orchestrator that decomposes complex tasks into subtasks.

Available workers: {', '.join(available_workers)}
- research: Information gathering, documentation, sources
- coder: Code generation, programming tasks
- analyst: Data analysis, insights, reasoning

Decompose the task into subtasks and assign each to the most appropriate worker.
Return JSON array of subtasks with this structure:
[
  {{"worker": "worker_name", "task": "specific subtask", "reasoning": "why this worker"}},
  ...
]

Rules:
- Break down into 1-4 subtasks based on complexity
- Each subtask should be independent and parallelizable
- Choose the best worker for each subtask based on its specialty
- Include reasoning for each worker assignment
"""
    
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=f"Task: {task}\n\nDecompose this into subtasks with worker assignments.",
        config={
            "system_instruction": system_instruction
        }
    )
    
    try:
        subtasks = json.loads(response.text)
    except json.JSONDecodeError:
        subtasks = [{"worker": "research", "task": task, "reasoning": "Fallback to single research task"}]
    
    return {"subtasks": subtasks}

def delegate_tasks(state: AgentState) -> AgentState:
    """Execute subtasks in parallel using ThreadPoolExecutor."""
    subtasks = state["subtasks"]
    max_workers = int(os.getenv("MAX_WORKERS", "3"))
    worker_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_subtask = {}
        
        for subtask in subtasks:
            worker_func = get_worker(subtask["worker"])
            future = executor.submit(worker_func, subtask["task"])
            future_to_subtask[future] = subtask
        
        for future in as_completed(future_to_subtask):
            subtask = future_to_subtask[future]
            try:
                result = future.result()
                worker_results.append(result)
            except Exception as e:
                retry_future = executor.submit(get_worker(subtask["worker"]), subtask["task"])
                try:
                    result = retry_future.result()
                    worker_results.append(result)
                except Exception as retry_error:
                    worker_results.append({
                        "worker": subtask["worker"],
                        "task": subtask["task"],
                        "error": str(retry_error),
                        "status": "failed"
                    })
    
    return {"worker_results": worker_results}

def synthesize_results(state: AgentState) -> AgentState:
    """Synthesize worker results into coherent final output."""
    task = state["task"]
    results = state["worker_results"]
    
    system_instruction = """You are a synthesis specialist.

Combine worker results into a coherent, comprehensive final response.
- Integrate information from all workers smoothly
- Present code, research, and analysis in a logical flow
- Maintain clarity and readability
- Acknowledge if any worker failed and work with available results
"""
    
    results_text = json.dumps(results, indent=2)
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=f"Original task: {task}\n\nWorker results:\n{results_text}\n\nSynthesize these into a comprehensive final answer.",
        config={
            "system_instruction": system_instruction
        }
    )
    
    return {"final_output": response.text}

def build_graph():
    """Build the LangGraph orchestration workflow."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("decompose", decompose_task)
    workflow.add_node("delegate", delegate_tasks)
    workflow.add_node("synthesize", synthesize_results)
    
    workflow.set_entry_point("decompose")
    workflow.add_edge("decompose", "delegate")
    workflow.add_edge("delegate", "synthesize")
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()

def run_orchestrator(task: str) -> str:
    """Run the orchestrator on a task and return final output."""
    graph = build_graph()
    
    initial_state: AgentState = {
        "task": task,
        "subtasks": [],
        "worker_results": [],
        "final_output": ""
    }
    
    final_state = graph.invoke(initial_state)
    return final_state["final_output"]
