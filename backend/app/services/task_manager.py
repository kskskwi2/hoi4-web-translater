import uuid
import time
from typing import Dict, Any

# Global task storage
# Structure: { "task_id": { ...status... } }
_tasks: Dict[str, Dict[str, Any]] = {}


def create_task() -> str:
    """Creates a new task and returns its ID."""
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {
        "id": task_id,
        "status": "pending",  # pending, running, completed, error
        "created_at": time.time(),
        "percent": 0,
        "current_file": "",
        "processed_files": 0,
        "total_files": 0,
        "current_entry": 0,
        "total_entries": 0,
        "entries_translated": 0,
        "avg_speed": 0,
        "start_time": 0,
        "error": None,
        "path": None,
        "zip_name": None,
    }
    return task_id


def get_task(task_id: str) -> Dict[str, Any]:
    """Returns task status or None if not found."""
    return _tasks.get(task_id)


def update_task(task_id: str, updates: Dict[str, Any]):
    """Updates task fields."""
    if task_id in _tasks:
        _tasks[task_id].update(updates)


def get_all_tasks():
    """Returns all tasks (for debug)."""
    return _tasks
