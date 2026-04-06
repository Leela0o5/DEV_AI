import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from workers import research, coder, analyst, get_worker, list_workers

def test_list_workers():
    workers = list_workers()
    assert len(workers) == 3
    assert "research" in workers
    assert "coder" in workers
    assert "analyst" in workers

def test_get_worker():
    research_worker = get_worker("research")
    assert callable(research_worker)
    
    with pytest.raises(ValueError):
        get_worker("invalid_worker")

def test_worker_execution():
    """Test that workers can execute and return structured data."""
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")
    
    result = research.execute("What is Python?")
    assert "worker" in result
    assert result["worker"] == "research"
    assert "task" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
