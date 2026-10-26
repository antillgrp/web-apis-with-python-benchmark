"""OpenAPI 3.0 specification and Swagger UI template for Flask Todo Task API."""

OPENAPI_SPEC = {
    "openapi": "3.0.2",
    "info": {
        "title": "Flask Todo Task API",
        "description": "Todo Task Management API built with Flask and shared SQLite (todos.db)",
        "version": "1.0.0",
    },
    "paths": {
        "/api/tasks": {
            "get": {
                "summary": "Get Tasks",
                "description": "Fetch the list of all tasks",
                "operationId": "get_tasks_api_tasks_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/TaskList"},
                                }
                            }
                        },
                    }
                },
            }
        },
        "/api/tasks/{id}": {
            "get": {
                "summary": "Get Task",
                "description": "Fetch the task by id",
                "operationId": "get_task_api_tasks__id__get",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer", "title": "Id"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TaskList"}
                            }
                        },
                    },
                    "404": {"description": "Task Not Found"},
                },
            }
        },
        "/api/tasks/create": {
            "post": {
                "summary": "Create Task",
                "description": "1. Create a new task and\n2. Return the details of task",
                "operationId": "create_task_api_tasks_create_post",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Task"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TaskList"}
                            }
                        },
                    },
                    "422": {"description": "Validation Error"},
                },
            }
        },
        "/api/tasks/{id}/update": {
            "put": {
                "summary": "Update Task",
                "description": "1. Update the task by id\n2. Return the updated task",
                "operationId": "update_task_api_tasks__id__update_put",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer", "title": "Id"},
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Task"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TaskList"}
                            }
                        },
                    },
                    "404": {"description": "Task Not Found"},
                    "422": {"description": "Validation Error"},
                },
            }
        },
        "/api/tasks/{id}/delete": {
            "delete": {
                "summary": "Delete Task",
                "description": "1. Delete the task by id\n2. Return a confirmation of deletion",
                "operationId": "delete_task_api_tasks__id__delete_delete",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer", "title": "Id"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
    },
    "components": {
        "schemas": {
            "Task": {
                "title": "Task",
                "required": ["summary", "priority"],
                "type": "object",
                "properties": {
                    "summary": {"title": "Summary", "type": "string"},
                    "priority": {
                        "title": "Priority",
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 4,
                        "description": "Priority scale from 1 to 4, 1 being highest",
                    },
                },
            },
            "TaskList": {
                "title": "TaskList",
                "required": ["id", "task"],
                "type": "object",
                "properties": {
                    "id": {"title": "Id", "type": "integer"},
                    "task": {"$ref": "#/components/schemas/Task"},
                },
            },
        }
    },
}

SWAGGER_UI_HTML = """<!DOCTYPE html>
<html>
<head>
    <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    <title>Flask Todo Task API - Swagger UI</title>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
    const ui = SwaggerUIBundle({
        url: '/api/openapi.json',
        dom_id: '#swagger-ui',
        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout",
        deepLinking: true
    });
    </script>
</body>
</html>
"""
