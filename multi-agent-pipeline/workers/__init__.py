from typing import Dict, Callable, Any
from . import research, coder, analyst

WORKERS: Dict[str, Callable[[str], Dict[str, Any]]] = {
    "research": research.execute,
    "coder": coder.execute,
    "analyst": analyst.execute,
}

def get_worker(name: str) -> Callable[[str], Dict[str, Any]]:
    """Get worker function by name."""
    if name not in WORKERS:
        raise ValueError(f"Unknown worker: {name}. Available: {list(WORKERS.keys())}")
    return WORKERS[name]

def list_workers() -> list[str]:
    """List all available worker names."""
    return list(WORKERS.keys())
