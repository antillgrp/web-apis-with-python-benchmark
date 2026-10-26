import logging
from flask import Flask, Response, jsonify, request
from pydantic import ValidationError
from model.model import Task, TaskList
from model.swagger import OPENAPI_SPEC, SWAGGER_UI_HTML
import model.taskman as taskman


class ServerTagFormatter(logging.Formatter):
    """Prefix every Flask / Werkzeug log entry with [FLASK :5000]."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return "\n".join(
            f"\033[1;36m[FLASK   :5000]\033[0m {line}" for line in msg.splitlines()
        )


def configure_flask_logging() -> None:
    """Attach the [FLASK :5000] formatter to Werkzeug and root loggers."""
    handler = logging.StreamHandler()
    handler.setFormatter(ServerTagFormatter("%(message)s"))
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers = [handler]
    werkzeug_logger.setLevel(logging.DEBUG)
    werkzeug_logger.propagate = False


configure_flask_logging()

app = Flask(__name__)
app.debug = True


@app.get("/api/openapi.json")
def openapi_spec():
    """Serve OpenAPI 3.0 specification for Swagger UI."""
    return jsonify(OPENAPI_SPEC)


@app.get("/api/doc")
def swagger_ui():
    """Serve interactive Swagger UI documentation at /api/doc."""
    return Response(SWAGGER_UI_HTML, mimetype="text/html")


# ===========================================================================
# 1. Sequential / Synchronous Endpoints (/api/tasks & /api/seq/tasks)
# ===========================================================================

@app.get("/api/tasks")
@app.get("/api/seq/tasks")
def get_tasks_seq():
    """Fetch the list of all tasks (Sequential/Synchronous endpoint)."""
    tasks = taskman.get_tasks_sync()
    return jsonify(tasks)


@app.get("/api/tasks/<int:id>")
@app.get("/api/seq/tasks/<int:id>")
def get_task_seq(id: int):
    """Fetch the task by id (Sequential/Synchronous endpoint)."""
    task = taskman.get_tasks_sync(id)
    if task is None:
        return jsonify({"detail": f"Task {id} not found"}), 404
    return jsonify(task)


@app.post("/api/tasks/create")
@app.post("/api/seq/tasks/create")
def create_task_seq():
    """Create a new task and return its details (Sequential/Synchronous endpoint)."""
    payload = request.get_json(silent=True) or {}
    try:
        task = Task(**payload)
    except ValidationError as exc:
        return jsonify({"detail": exc.errors()}), 422

    created = taskman.create_task_sync(task)
    return jsonify(created)


@app.put("/api/tasks/<int:id>/update")
@app.put("/api/seq/tasks/<int:id>/update")
def update_task_seq(id: int):
    """Update the task by id and return the updated task (Sequential/Synchronous endpoint)."""
    payload = request.get_json(silent=True) or {}
    try:
        task = Task(**payload)
    except ValidationError as exc:
        return jsonify({"detail": exc.errors()}), 422

    updated = taskman.update_task_sync(id, task)
    if updated is None:
        return jsonify({"detail": f"Task {id} not found"}), 404
    return jsonify(updated)


@app.delete("/api/tasks/<int:id>/delete")
@app.delete("/api/seq/tasks/<int:id>/delete")
def delete_task_seq(id: int):
    """Delete the task by id and return confirmation (Sequential/Synchronous endpoint)."""
    result = taskman.delete_task_sync(id)
    return jsonify(result)


# ===========================================================================
# 2. Asynchronous Endpoints (/api/async/tasks)
# ===========================================================================

@app.get("/api/async/tasks")
async def get_tasks_async():
    """Fetch the list of all tasks (Asynchronous route on Flask)."""
    tasks = await taskman.get_tasks()
    return jsonify(tasks)


@app.get("/api/async/tasks/<int:id>")
async def get_task_async(id: int):
    """Fetch the task by id (Asynchronous route on Flask)."""
    task = await taskman.get_tasks(id)
    if task is None:
        return jsonify({"detail": f"Task {id} not found"}), 404
    return jsonify(task)


@app.post("/api/async/tasks/create")
async def create_task_async():
    """Create a new task and return its details (Asynchronous route on Flask)."""
    payload = request.get_json(silent=True) or {}
    try:
        task = Task(**payload)
    except ValidationError as exc:
        return jsonify({"detail": exc.errors()}), 422

    created = await taskman.create_task(task)
    return jsonify(created)


@app.put("/api/async/tasks/<int:id>/update")
async def update_task_async(id: int):
    """Update the task by id and return the updated task (Asynchronous route on Flask)."""
    payload = request.get_json(silent=True) or {}
    try:
        task = Task(**payload)
    except ValidationError as exc:
        return jsonify({"detail": exc.errors()}), 422

    updated = await taskman.update_task(id, task)
    if updated is None:
        return jsonify({"detail": f"Task {id} not found"}), 404
    return jsonify(updated)


@app.delete("/api/async/tasks/<int:id>/delete")
async def delete_task_async(id: int):
    """Delete the task by id and return confirmation (Asynchronous route on Flask)."""
    result = await taskman.delete_task(id)
    return jsonify(result)


if __name__ == "__main__":
    # Run in debug mode and synchronous/sequential mode (threaded=False)
    import flask.cli

    flask.cli.show_server_banner = lambda *args, **kwargs: logging.getLogger(
        "werkzeug"
    ).info(" * Serving Flask app 'flask_api_srv'\n * Debug mode: on")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=False, use_reloader=False)
