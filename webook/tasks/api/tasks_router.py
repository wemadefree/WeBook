from typing import Any, Dict, List, Optional
from uuid import UUID
from django.db.models.query import QuerySet
from django.http import HttpResponse
from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.api.session_auth import AuthAgent
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


class TaskExecutionSchema(BaseSchema):
    uuid: UUID
    task_name: str
    status: TaskExecutionState
    parameters: Dict[str, Any] = {}
    result: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None

    @classmethod
    def from_model(cls, task_execution: TaskExecution) -> "TaskExecutionSchema":
        return cls(
            id=task_execution.id,
            uuid=task_execution.uuid,
            task_name=task_execution.task_name,
            status=task_execution.status,
            parameters=task_execution.parameters,
            result=task_execution.result,
            created_at=task_execution.created_at.isoformat(),
            updated_at=task_execution.updated_at.isoformat(),
            completed_at=(
                task_execution.completed_at.isoformat()
                if task_execution.completed_at
                else None
            ),
        )


@tasks_router.get("/get-tasks", response=List[TaskSchema], auth=AuthAgent())
def get_tasks(request) -> List[TaskSchema]:
    """
    Endpoint to retrieve a list of tasks.
    """
    return [
        TaskSchema(name=t.name, description=t.description, parameters=t.parameters)
        for t in TASK_MANAGER.list_tasks()
    ]


@tasks_router.post("/stage-task", response=str, auth=AuthAgent())
def start_task(request, task_name: str, task_params: dict = {}) -> str:
    """
    Endpoint to start a task.
    """

    task_params = {k: v for k, v in request.GET.items() if k != "task_name"}

    if not TASK_MANAGER.task_exists(task_name):
        return HttpResponse(status=404, content=f"Task '{task_name}' not found.")
    try:
        task_execution = TASK_MANAGER.stage_task(
            task_name=task_name, parameters=task_params
        )
        return str(task_execution.uuid)
    except Exception as e:
        return HttpResponse(status=500, content=f"Failed to stage task: {str(e)}")


@tasks_router.get(
    "/get-pending-tasks", response=List[TaskExecutionSchema], auth=AuthAgent()
)
def get_pending_tasks(request) -> List[TaskExecutionSchema]:
    """
    Endpoint to get a list of pending tasks.
    """
    pending_tasks = TaskExecution.objects.filter(status="pending")

    return [TaskExecutionSchema.from_model(task) for task in pending_tasks]


@tasks_router.get("/task/{task_id}", response=TaskExecutionSchema, auth=AuthAgent())
def get_task_execution_record(request, task_uuid: str) -> TaskExecutionSchema:
    """
    Endpoint to get the execution record of a specific task by its ID.
    """

    task_execution = TaskExecution.objects.filter(uuid=task_uuid).first()
    if not task_execution:
        return HttpResponse(
            status=404, content=f"Task with UUID '{task_uuid}' not found."
        )

    return TaskExecutionSchema.from_model(task_execution)


@tasks_router.post("/execute-task", response=bool, auth=None)
def execute_task(request, task_uuid: str) -> bool:
    """
    Endpoint to execute a specific task.
    """

    task_execution = TaskExecution.objects.filter(uuid=task_uuid).first()
    if not task_execution:
        return HttpResponse(
            status=404, content=f"Task with UUID '{task_uuid}' not found."
        )

    task_execution.status = TaskExecutionState.RUNNING
    task_execution.save()

    try:
        TASK_MANAGER.execute_task(task_execution)
        return True
    except Exception as e:
        task_execution.status = TaskExecutionState.FAILED
        task_execution.result = str(e)
        task_execution.save()

        return HttpResponse(status=500, content=f"Failed to execute task: {str(e)}")
