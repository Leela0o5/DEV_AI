import os
import subprocess
from typing import List

# Restrict operations to the workspace directory for sandboxing
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace"))

def _resolve_path(filepath: str) -> str:
    """Safely resolve paths to ensure they stay inside the workspace."""
    # Normalize path and prevent directory traversal
    safe_path = os.path.normpath(filepath).lstrip("\\/")
    return os.path.join(WORKSPACE_DIR, safe_path)

def list_files(directory: str = ".") -> List[str]:
    """Returns a list of all recursive files in the given directory within the workspace."""
    target_path = _resolve_path(directory)
    if not os.path.exists(target_path):
        return [f"Error: Directory {directory} does not exist."]
    
    files = []
    for root, _, filenames in os.walk(target_path):
        if "__pycache__" in root or ".pytest_cache" in root:
            continue
        for filename in filenames:
            rel_dir = os.path.relpath(root, target_path)
            if rel_dir == ".":
                files.append(filename)
            else:
                files.append(os.path.join(rel_dir, filename).replace("\\", "/"))
    return files

def read_file(filepath: str) -> str:
    """Reads and returns the content of a file in the workspace."""
    target_path = _resolve_path(filepath)
    if not os.path.exists(target_path):
        return f"Error: File {filepath} does not exist."
    try:
         with open(target_path, "r", encoding="utf-8") as f:
             return f.read()
    except Exception as e:
         return f"Error reading file: {e}"

def write_file(filepath: str, content: str) -> str:
    """Overwrites or creates a file in the workspace with the given content."""
    target_path = _resolve_path(filepath)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing to file: {e}"

def run_tests() -> str:
    """
    Runs pytest in the workspace to verify the code correctness.
    Returns structured results including pass/fail status, exit code, and tracebacks.
    """
    target_dir = WORKSPACE_DIR
    try:
        result = subprocess.run(
            ["pytest", "-v"],
            cwd=target_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        status = "PASSED" if result.returncode == 0 else "FAILED"
        return f"=== TEST RESULTS ===\nStatus: {status}\nExit Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "=== TEST RESULTS ===\nERROR: Execution timed out after 10 seconds. Your code likely has an infinite loop."
    except FileNotFoundError:
        return "=== TEST RESULTS ===\nERROR: pytest is not installed or not found in the environment."
    except Exception as e:
        return f"=== TEST RESULTS ===\nERROR running tests: {e}"

def task_complete() -> str:
    """Call this explicitly only when you are 100% finished with the user's task and all tests are passing."""
    return "TASK_COMPLETE_SIGNAL"
