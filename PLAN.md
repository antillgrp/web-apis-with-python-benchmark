# Flask vs FastAPI Todo App Benchmarking — Master Plan

> **Branch**: `flask_fastapi_todo_app_benchmarking`  
> **Virtual Environment**: Single shared `~/.venvs/web-apis-env` (Python 3.15)  
> **Database**: Shared SQLite `todos.db` (WAL mode)  
> **Servers**: Flask (`0.0.0.0:8080`) & FastAPI (`0.0.0.0:8090`)  
> **Swagger UI**: `http://127.0.0.1:8080/api/doc` & `http://127.0.0.1:8090/api/doc`

---

## 1. Progress Tracker

### Phase 1: Plan & Git / GitHub Setup
- [x] **1.1** Create and maintain [`PLAN.md`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/PLAN.md)
- [x] **1.2** Create and checkout branch `flask_fastapi_todo_app_benchmarking`
- [ ] **1.3** Authenticate to GitHub, create remote repository in user's GitHub, and set `origin`

### Phase 2: Dependencies & Shared Virtual Environment (`~/.venvs/web-apis-env`)
- [x] **2.1** Create [`flask_requeriments.txt`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/flask_requeriments.txt)
- [x] **2.2** Create [`fastapi_requeriments.txt`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/fastapi_requeriments.txt)
- [x] **2.3** Install both requirement files into `~/.venvs/web-apis-env`

### Phase 3: Top-Down Model & SQLite Persistence Layer (`model/` + `todos.db`)
- [x] **3.1** Create [`model/__init__.py`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/model/__init__.py) and [`model/model.py`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/model/model.py) (`ID`, `Task`, `TaskList`)
- [x] **3.2** Create [`model/task_service.py`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/model/task_service.py) backed by shared SQLite `todos.db` (`WAL` mode)

### Phase 4: API Servers & Swagger UI (`/api/doc`)
- [x] **4.1** Create [`fastapi_api_controller.py`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/fastapi_api_controller.py) (Port `8090` + Swagger UI at `/api/doc`)
- [x] **4.2** Create [`flask_api_controller.py`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/flask_api_controller.py) (Port `8080` + Swagger UI at `/api/doc`)

### Phase 5: Parallel Execution & Multi-Core Benchmarking (`xargs -r -P`)
- [x] **5.1** Create [`run_servers.sh`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/run_servers.sh) (launches Flask `:8080` & FastAPI `:8090` in parallel via `xargs -r -P 2`)
- [x] **5.2** Create [`benchmark_parallel.sh`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/benchmark_parallel.sh) implementing the 4 Benchmark Test Scenarios (10 API calls each):
  - **Test Scenario 1**: Sequential API calls (`-P 1`) to sequential API endpoint (`Flask :8080`)
  - **Test Scenario 2**: Asynchronous/Simultaneous API calls (`xargs -r -P 10`) to sequential API endpoint (`Flask :8080`)
  - **Test Scenario 3**: Sequential API calls (`-P 1`) to asynchronous API endpoint (`FastAPI :8090`)
  - **Test Scenario 4**: Asynchronous/Simultaneous API calls (`xargs -r -P 10`) to asynchronous API endpoint (`FastAPI :8090`)

### Phase 6: Verification & Git Push
- [x] **6.1** Verify endpoints, shared `todos.db` state, and Swagger UI (`/api/doc`)
- [ ] **6.2** Commit all changes and push to `origin/flask_fastapi_todo_app_benchmarking`

---

## 2. Target Project Structure

```text
web-apis-with-python/
├── README.md                    # Documentation on running servers & benchmarks
├── PLAN.md                      # Master plan & live progress tracker
├── flask_requeriments.txt       # Flask dependencies (Python 3.15 compatible)
├── fastapi_requeriments.txt     # FastAPI dependencies (Python 3.15 compatible)
├── flask_api_controller.py      # Flask Todo API controller (Port 8080, Swagger on /api/doc)
├── fastapi_api_controller.py    # FastAPI Todo API controller (Port 8090, Swagger on /api/doc)
├── run_servers.sh               # Parallel launcher using xargs -r -P 2
├── benchmark_parallel.sh        # Multi-core parallel benchmark using xargs -r -P 4
├── todos.db                     # Shared SQLite database (auto-initialized, WAL mode)
├── model/
│   ├── __init__.py
│   ├── model.py                 # Pydantic models: ID, Task, TaskList
│   ├── swagger.py               # OpenAPI 3.0 spec & Swagger UI template for Flask
│   └── task_service.py          # Top-down task service using SQLite todos.db
└── env/                         # Single shared Python virtual environment
```

---

## 3. Technical Specifications

### 3.1 API Specifications (Section 14.1)
1. **Create a new task** containing:
   - **ID (`id`)**: Unique integer identifier for the task (`ID = NewType("id", int)`)
   - **Summary (`summary`)**: Description of the task (`str`)
   - **Priority (`priority`)**: Integer scale from `1` to `4` (`1` being highest)
2. **Modify a task**: Update task `summary` and/or `priority` by `id`
3. **Delete a task**: Delete a task by `id`
4. **Fetch tasks**: List all tasks or fetch a single task by `id`

### 3.2 Data Models (`model/model.py`)
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import NewType, Optional

# Declare a new type of variable ID
ID = NewType("id", int)


class Task(BaseModel):
    """Definition of components of a task"""
    summary: str
    priority: int = Field(..., ge=1, le=4, description="Priority scale from 1 to 4, 1 being highest")
    # due_date: Optional[datetime]


class TaskList(BaseModel):
    """Definition of the TaskList"""
    id: ID
    task: Task
```

### 3.3 Top-Down Task Service (`model/task_service.py` + `todos.db`)
Replaces the JSON file backend with SQLite (`todos.db`) while preserving the exact route handler interface:

| Function Signature | Behavior |
| :--- | :--- |
| `async def get_tasks(id: Optional[int] = 0)` | Fetch all tasks (`List[TaskList]`) if `id == 0`, else fetch task by `id` |
| `async def create_task(new_task: Task)` | Insert `new_task` into `todos.db` and return the created `TaskList` (with `id`) |
| `async def update_task(id: int, new_task: Task)` | Update `summary` & `priority` for `id` in `todos.db` and return updated `TaskList` |
| `async def delete_task(id: int)` | Delete task `id` from `todos.db` and return confirmation with `id` |

### 3.4 API Endpoints & Swagger UI (`flask_api_controller.py` & `fastapi_api_controller.py`)

| Method | Route | Handler Call | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/doc` | Swagger UI | Interactive OpenAPI / Swagger UI documentation |
| `GET` | `/api/openapi.json` | OpenAPI Schema | OpenAPI 3.0 JSON specification |
| `GET` | `/api/tasks` | `await task_service.get_tasks()` | Fetch the list of all tasks |
| `GET` | `/api/tasks/{id}` | `await task_service.get_tasks(id)` | Fetch a single task by `id` |
| `POST` | `/api/tasks/create` | `await task_service.create_task(task)` | Create a new task and return its details with `id` |
| `PUT` | `/api/tasks/{id}/update` | `await task_service.update_task(id, task)` | Update a specific task by `id` and return updated task |
| `DELETE` | `/api/tasks/{id}/delete` | `await task_service.delete_task(id)` | Delete the task by `id` and return confirmation |
