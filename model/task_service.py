import asyncio
import os
import shutil
import sqlite3
import tempfile
import time
from typing import List, Optional, Union
from model.model import ID, Task, TaskList

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DB_PATH = os.path.join(BASE_DIR, "todos.db")


def _resolve_db_path() -> str:
    """
    Use a local filesystem path (/tmp/web-apis-with-python-benchmark/todos.db) by default
    so SQLite WAL shared-memory locking (.db-shm / .db-wal) never fails with
    'sqlite3.OperationalError: locking protocol' when the project resides on an
    SMB/CIFS or WSL drvfs network mount.
    """
    env_db = os.environ.get("TASK_SERVICE_DB_PATH") or os.environ.get("TASKMAN_DB_PATH")
    if env_db:
        return env_db

    local_dir = os.path.join(tempfile.gettempdir(), "web-apis-with-python-benchmark")
    os.makedirs(local_dir, exist_ok=True)
    local_db = os.path.join(local_dir, "todos.db")

    if not os.path.exists(local_db) and os.path.exists(SOURCE_DB_PATH):
        try:
            shutil.copy2(SOURCE_DB_PATH, local_db)
        except OSError:
            pass

    return local_db


DB_PATH = _resolve_db_path()

# Simulated I/O latency (seconds) to make synchronous blocking vs async non-blocking visible
IO_DELAY = float(
    os.environ.get("TASK_SERVICE_IO_DELAY", os.environ.get("TASKMAN_IO_DELAY", "0.05"))
)


def _get_connection() -> sqlite3.Connection:
    """Create a SQLite connection to todos.db configured with WAL mode for concurrency."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000;")
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except sqlite3.OperationalError:
        conn.execute("PRAGMA journal_mode=MEMORY;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db() -> None:
    """Initialize the shared SQLite todos.db database and tasks table."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT NOT NULL,
                priority INTEGER NOT NULL CHECK(priority >= 1 AND priority <= 4)
            );
            """
        )
        conn.commit()


def _row_to_tasklist_dict(row: sqlite3.Row) -> dict:
    """Convert a SQLite row into a serialized TaskList dictionary."""
    task_item = TaskList(
        id=ID(row["id"]),
        task=Task(summary=row["summary"], priority=row["priority"]),
    )
    return task_item.model_dump() if hasattr(task_item, "model_dump") else task_item.dict()


# Ensure database and table exist on module load
init_db()


# ---------------------------------------------------------------------------
# Synchronous / Sequential handlers (blocks the current thread during I/O)
# ---------------------------------------------------------------------------

def _db_get_tasks(id: Optional[int] = 0) -> Union[List[dict], dict, None]:
    with _get_connection() as conn:
        if not id:
            cursor = conn.execute(
                "SELECT id, summary, priority FROM tasks ORDER BY id ASC"
            )
            rows = cursor.fetchall()
            return [_row_to_tasklist_dict(row) for row in rows]
        else:
            cursor = conn.execute(
                "SELECT id, summary, priority FROM tasks WHERE id = ?",
                (id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return _row_to_tasklist_dict(row)


def _db_create_task(new_task: Task) -> dict:
    with _get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (summary, priority) VALUES (?, ?)",
            (new_task.summary, new_task.priority),
        )
        conn.commit()
        new_id = cursor.lastrowid

    created = TaskList(id=ID(new_id), task=new_task)
    return created.model_dump() if hasattr(created, "model_dump") else created.dict()


def _db_update_task(id: int, new_task: Task) -> Optional[dict]:
    with _get_connection() as conn:
        cursor = conn.execute(
            "UPDATE tasks SET summary = ?, priority = ? WHERE id = ?",
            (new_task.summary, new_task.priority, id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None

    updated = TaskList(id=ID(id), task=new_task)
    return updated.model_dump() if hasattr(updated, "model_dump") else updated.dict()


def _db_delete_task(id: int) -> dict:
    with _get_connection() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (id,))
        conn.commit()
        deleted = cursor.rowcount > 0

    return {
        "id": id,
        "deleted": deleted,
        "message": f"Task {id} deleted" if deleted else f"Task {id} not found",
    }


def get_tasks_sync(id: Optional[int] = 0) -> Union[List[dict], dict, None]:
    """Sequential/Synchronous task fetch (blocks with time.sleep)."""
    if IO_DELAY > 0:
        time.sleep(IO_DELAY)
    return _db_get_tasks(id)


def create_task_sync(new_task: Task) -> dict:
    """Sequential/Synchronous task creation (blocks with time.sleep)."""
    if IO_DELAY > 0:
        time.sleep(IO_DELAY)
    return _db_create_task(new_task)


def update_task_sync(id: int, new_task: Task) -> Optional[dict]:
    """Sequential/Synchronous task update (blocks with time.sleep)."""
    if IO_DELAY > 0:
        time.sleep(IO_DELAY)
    return _db_update_task(id, new_task)


def delete_task_sync(id: int) -> dict:
    """Sequential/Synchronous task deletion (blocks with time.sleep)."""
    if IO_DELAY > 0:
        time.sleep(IO_DELAY)
    return _db_delete_task(id)


# ---------------------------------------------------------------------------
# Asynchronous handlers (non-blocking await asyncio.sleep + asyncio.to_thread)
# ---------------------------------------------------------------------------

async def get_tasks(id: Optional[int] = 0) -> Union[List[dict], dict, None]:
    """
    1. Fetch all tasks if no argument (id) provided
    2. Else fetch the task by id provided
    """
    if IO_DELAY > 0:
        await asyncio.sleep(IO_DELAY)
    return await asyncio.to_thread(_db_get_tasks, id)


async def create_task(new_task: Task) -> dict:
    """
    1. Create a new task and add it to the database (todos.db)
    2. Return the created TaskList details including id
    """
    if IO_DELAY > 0:
        await asyncio.sleep(IO_DELAY)
    return await asyncio.to_thread(_db_create_task, new_task)


async def update_task(id: int, new_task: Task) -> Optional[dict]:
    """
    1. Update the task by id based on new task details in todos.db
    2. Return the updated task
    """
    if IO_DELAY > 0:
        await asyncio.sleep(IO_DELAY)
    return await asyncio.to_thread(_db_update_task, id, new_task)


async def delete_task(id: int) -> dict:
    """
    1. Delete the task by id provided from todos.db
    2. Return a confirmation of deletion
    """
    if IO_DELAY > 0:
        await asyncio.sleep(IO_DELAY)
    return await asyncio.to_thread(_db_delete_task, id)
