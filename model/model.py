from pydantic import BaseModel, Field
from datetime import datetime
from typing import NewType, Optional

# Declare a new type of variable ID
ID = NewType("id", int)


class Task(BaseModel):
    """Definition of components of a task"""

    summary: str
    priority: int = Field(
        ..., ge=1, le=4, description="Priority scale from 1 to 4, 1 being highest"
    )
    # due_date: Optional[datetime]


class TaskList(BaseModel):
    """Definition of the TaskList"""

    id: ID
    task: Task
