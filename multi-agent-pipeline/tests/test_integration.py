import pytest
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator import run_orchestrator, decompose_task, delegate_tasks, AgentState
from workers import get_worker

def test_end_to_end():
    """Test full orchestration pipeline."""
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")
    
    task = "Explain what a Python decorator is and write a simple example"
    result = run_orchestrator(task)
    
    assert isinstance(result, str)
    assert len(result) > 100
    print(f"\n\nFinal Result:\n{result}\n")

def test_parallel_execution():
    """Verify parallel execution is faster than sequential."""
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")
    
    tasks = [
        ("research", "What is asyncio?"),
        ("coder", "Write hello world"),
        ("analyst", "Analyze 1+1")
    ]
    
    # Parallel execution
    start_parallel = time.time()
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(get_worker(w), t) for w, t in tasks]
        results_parallel = [f.result() for f in as_completed(futures)]
    parallel_time = time.time() - start_parallel
    
    # Sequential execution
    start_sequential = time.time()
    results_sequential = [get_worker(w)(t) for w, t in tasks]
    sequential_time = time.time() - start_sequential
    
    print(f"\nParallel time: {parallel_time:.2f}s")
    print(f"Sequential time: {sequential_time:.2f}s")
    print(f"Speedup: {sequential_time/parallel_time:.2f}x")
    
    assert len(results_parallel) == 3
    assert len(results_sequential) == 3
    assert parallel_time < sequential_time

def test_task_decomposition():
    """Test that tasks are properly decomposed."""
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")
    
    state: AgentState = {
        "task": "Research Python and write code",
        "subtasks": [],
        "worker_results": [],
        "final_output": ""
    }
    
    result = decompose_task(state)
    subtasks = result["subtasks"]
    
    assert len(subtasks) > 0
    for subtask in subtasks:
        assert "worker" in subtask
        assert "task" in subtask
        assert "reasoning" in subtask
    
    print(f"\n\nDecomposed into {len(subtasks)} subtasks:")
    for i, st in enumerate(subtasks, 1):
        print(f"{i}. {st['worker']}: {st['task']}")
        print(f"   Reasoning: {st['reasoning']}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
