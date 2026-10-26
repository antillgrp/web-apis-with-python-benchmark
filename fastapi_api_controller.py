import copy
from fastapi import FastAPI, HTTPException
from datetime import datetime
from typing import Optional
from fastapi.encoders import jsonable_encoder
from model.model import Task, TaskList
import model.task_service as task_service
import uvicorn
from uvicorn.config import LOGGING_CONFIG

app = FastAPI(
    title="FastAPI Todo Task API",
    description="Todo Task Management API built with FastAPI and shared SQLite (todos.db)",
    version="1.0.0",
    debug=True,
    docs_url="/api/doc",
    openapi_url="/api/openapi.json",
)


# ===========================================================================
# 1. Asynchronous Endpoints (/api/tasks & /api/async/tasks)
# ===========================================================================

@app.get("/api/tasks")
@app.get("/api/async/tasks")
async def get_tasks():
    """Fetch the list of all tasks (Asynchronous non-blocking endpoint)."""
    tasks = await task_service.get_tasks()
    return jsonable_encoder(tasks)


@app.get("/api/tasks/{id}")
@app.get("/api/async/tasks/{id}")
async def get_task(id: int):
    """Fetch the task by id (Asynchronous non-blocking endpoint)."""
    task = await task_service.get_tasks(id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    return jsonable_encoder(task)


@app.post("/api/tasks/create")
@app.post("/api/async/tasks/create")
async def create_task(task: Task):
    """Create a new task and return its details (Asynchronous non-blocking endpoint)."""
    created = await task_service.create_task(task)
    return jsonable_encoder(created)


@app.put("/api/tasks/{id}/update")
@app.put("/api/async/tasks/{id}/update")
async def update_task(id: int, task: Task):
    """Update the task by id and return the updated task (Asynchronous non-blocking endpoint)."""
    updated = await task_service.update_task(id, task)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    return jsonable_encoder(updated)


@app.delete("/api/tasks/{id}/delete")
@app.delete("/api/async/tasks/{id}/delete")
async def delete_task(id: int):
    """Delete the task by id and return confirmation (Asynchronous non-blocking endpoint)."""
    result = await task_service.delete_task(id)
    return jsonable_encoder(result)


# ===========================================================================
# 2. Sequential / Synchronous Endpoints (/api/seq/tasks)
# ===========================================================================

@app.get("/api/seq/tasks")
async def get_tasks_seq():
    """Fetch the list of all tasks (Sequential blocking endpoint on FastAPI)."""
    tasks = task_service.get_tasks_sync()
    return jsonable_encoder(tasks)


@app.get("/api/seq/tasks/{id}")
async def get_task_seq(id: int):
    """Fetch the task by id (Sequential blocking endpoint on FastAPI)."""
    task = task_service.get_tasks_sync(id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    return jsonable_encoder(task)


@app.post("/api/seq/tasks/create")
async def create_task_seq(task: Task):
    """Create a new task and return its details (Sequential blocking endpoint on FastAPI)."""
    created = task_service.create_task_sync(task)
    return jsonable_encoder(created)


@app.put("/api/seq/tasks/{id}/update")
async def update_task_seq(id: int, task: Task):
    """Update the task by id and return the updated task (Sequential blocking endpoint on FastAPI)."""
    updated = task_service.update_task_sync(id, task)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    return jsonable_encoder(updated)


@app.delete("/api/seq/tasks/{id}/delete")
async def delete_task_seq(id: int):
    """Delete the task by id and return confirmation (Sequential blocking endpoint on FastAPI)."""
    result = task_service.delete_task_sync(id)
    return jsonable_encoder(result)


def get_uvicorn_log_config() -> dict:
    """Return Uvicorn logging config with [FASTAPI :8000] tag on every log line."""
    log_config = copy.deepcopy(LOGGING_CONFIG)
    tag = "\033[1;32m[FASTAPI :8000]\033[0m"
    log_config["formatters"]["default"]["fmt"] = f"{tag} %(levelprefix)s %(message)s"
    log_config["formatters"]["access"]["fmt"] = (
        f'{tag} %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    )
    return log_config


if __name__ == "__main__":
    # Run FastAPI asynchronously in debug mode on browser-safe port 8000
    print(
        "\033[1;32m[FASTAPI :8000]\033[0m  * Serving FastAPI app 'fastapi_api_controller' (Debug mode: on)",
        flush=True,
    )
    print(
        "\033[1;32m[FASTAPI :8000]\033[0m  * Running on http://127.0.0.1:8000 (Swagger UI: http://127.0.0.1:8000/api/doc)",
        flush=True,
    )
    uvicorn.run(
        "fastapi_api_controller:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="debug",
        log_config=get_uvicorn_log_config(),
    )
