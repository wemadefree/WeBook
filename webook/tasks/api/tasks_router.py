from typing import Any, Dict, List, Optional
from django.db.models.query import QuerySet
from django.http import HttpResponse
from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.arrangement.models import Person
from webook.graph_integration.models import GraphCalendar, SyncedEvent
from ninja import Router

from webook.tasks.models import TaskExecution, TaskExecutionState
from ..tasks_manager import TASK_MANAGER

tasks_router = Router(tags=["Tasks Backend"])


class TaskSchema(BaseSchema):
    name: str
    description: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None


@tasks_router.get("/get-tasks", response=List[TaskSchema])
def get_tasks(request) -> List[TaskSchema]:
    """
    Endpoint to retrieve a list of tasks.
    """
    return [
        TaskSchema(name=t.name, description=t.description, parameters=t.parameters)
        for t in TASK_MANAGER.list_tasks()
    ]


@tasks_router.get("/stage-task", response=bool)
def start_task(request, task_name: str) -> bool:
    """
    Endpoint to start a task.
    """

    if not TASK_MANAGER.task_exists(task_name):
        return HttpResponse(status=404, content=f"Task '{task_name}' not found.")
    try:
        TASK_MANAGER.stage_task(task_name=task_name, parameters=None)
        return True
    except Exception as e:
        return HttpResponse(status=500, content=f"Failed to stage task: {str(e)}")


@tasks_router.get("/get-pending-tasks", response=List[str])
def get_pending_tasks(request) -> List[str]:
    """
    Endpoint to get a list of pending tasks.
    """
    return TaskExecution.objects.filter(status="pending").values_list(
        "task_name", flat=True
    )


@tasks_router.get("/task-status/{task_id}", response=str)
def get_task_status(request, task_id: int) -> str:
    """
    Endpoint to get the status of a specific task.
    """
    return TASK_MANAGER.get_task_status(task_id)


@tasks_router.post("/execute-task", response=bool)
def execute_task(request, task_id: int) -> bool:
    """
    Endpoint to execute a specific task.
    """
    task_execution = TaskExecution.objects.filter(id=task_id).first()
    task_execution.status = TaskExecutionState.RUNNING
    task_execution.save()

    try:
        TASK_MANAGER.execute_task(task_id)
        return True
    except Exception as e:
        task_execution.status = TaskExecutionState.FAILED
        task_execution.result = str(e)
        task_execution.save()

        return HttpResponse(status=500, content=f"Failed to execute task: {str(e)}")
