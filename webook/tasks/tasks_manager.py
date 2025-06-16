import json
from typing import Any, Dict, List, Optional
from .models import TaskExecution, TaskExecutionState
from abc import ABC, abstractmethod
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from datetime import datetime
from django.conf import settings


class RegisteredTask:
    """
    Represents a registered task with its callable and metadata.
    """

    def __init__(self, callable, name: str, description: Optional[str] = None):
        self.callable = callable
        self.name = name
        self.description = description

    def __call__(self, *args, **kwargs):
        return self.callable(*args, **kwargs)


class TaskNotFoundError(Exception):
    """
    Exception raised when a task is not found.
    """

    def __init__(self, task_id: int):
        super().__init__(f"Task with ID {task_id} not found.")
        self.task_id = task_id


class TaskExeuctionCreateResponse:
    """
    Response schema for task execution creation.
    """

    success: bool
    task_id: int
    status: TaskExecutionState


class AbstractTaskBackend(ABC):
    """
    Abstract base class for task backends.
    """

    @abstractmethod
    def create_http_task(
        self,
        target_url: str,
        payload: Dict[str, Any],
        scheduled_seconds_from_now: Optional[int] = None,
        *args,
        **kwargs,
    ) -> TaskExeuctionCreateResponse:
        """
        Create a new HTTP task execution record.

        :param target_url: The URL to which the task will be sent.
        :return: True if the task was created successfully, False otherwise.
        """
        pass

    @abstractmethod
    def get_task_status(self, task_id: int) -> TaskExecutionState:
        """
        Get the status of a specific task.

        :param task_id: The ID of the task to check.
        :return: TaskExecution object containing the status and details of the task.
        """
        pass

    @abstractmethod
    def cancel_task(self, task_id: int) -> bool:
        """
        Cancel a specific task.

        :param task_id: The ID of the task to cancel.
        :return: True if the task was canceled successfully, False otherwise.
        """
        pass


class GoogleCloudTaskBackend(AbstractTaskBackend):
    """
    Google Cloud Task backend implementation.
    """

    def __init__(self, queue_name: str, project_id: str, location: str) -> None:
        """
        Initialize the Google Cloud Task backend.

        :param project_id: Google Cloud project ID.
        :param location: Location for the task queue.
        :param queeu_name: Name of the task queue.
        """
        self.project_id = project_id
        self.location = location
        self.queue_name = queue_name
        self.__client = tasks_v2.CloudTasksClient()

    def create_http_task(
        self,
        target_url: str,
        payload: Dict[str, Any],
        scheduled_seconds_from_now: Optional[int] = None,
        *args,
        **kwargs,
    ) -> bool:
        """
        Create a new HTTP task execution record in Google Cloud Tasks.

        :param target_url: The URL to which the task will be sent.
        :return: True if the task was created successfully, False otherwise.
        """
        task = tasks_v2.Task(
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=target_url,
                headers={
                    "Content-Type": "application/json",
                },
                body=json.dumps(payload).encode("utf-8"),
            ),
            name=None,
            # name=(
            #     self.__client.task_path(
            #         project=self.project_id,
            #         location=self.location,
            #         queue=self.queue_name,
            #     )
            # ),
        )

        if scheduled_seconds_from_now is not None:
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(
                datetime.datetime.utcnow()
                + datetime.timedelta(seconds=scheduled_seconds_from_now)
            )
            task.schedule_time = timestamp

        created_task = self.__client.create_task(
            tasks_v2.CreateTaskRequest(
                parent=self.__client.queue_path(
                    project=self.project_id,
                    location=self.location,
                    queue=self.queue_name,
                ),
                task=task,
            )
        )

        result = TaskExeuctionCreateResponse()
        result.success = True
        result.task_id = int(created_task.name.split("/")[-1])
        result.status = TaskExecutionState.PENDING

        return result

    def cancel_task(self, task_id: int) -> bool:
        """
        Cancel a specific task in Google Cloud Tasks.

        :param task_id: The ID of the task to cancel.
        :return: True if the task was canceled successfully, False otherwise.
        """
        try:
            self.__client.delete_task(
                tasks_v2.DeleteTaskRequest(
                    name=self.__client.task_path(
                        project=self.project_id,
                        location=self.location,
                        queue=self.queue_name,
                        task=task_id,
                    )
                )
            )
            return True
        except Exception as e:
            raise TaskNotFoundError(task_id) from e

    def get_task_status(self, task_id: int) -> TaskExecutionState:
        """
        Get the status of a specific task.

        :param task_id: The ID of the task to check.
        :return: TaskExecutionState object containing the status and details of the task.
        """
        # raise NotImplementedError(
        #     "GoogleCloudTaskBackend.get_task_status is not implemented yet."
        # )
        try:
            task: tasks_v2.Task = self.__client.get_task(
                tasks_v2.GetTaskRequest(
                    name=self.__client.task_path(
                        project=self.project_id,
                        location=self.location,
                        queue=self.queue_name,
                        task=task_id,
                    )
                )
            )
            return TaskExecutionState(task.status.name.lower())
        except Exception as e:
            raise TaskNotFoundError(task_id) from e


class TaskManager:
    def __init__(self, backend: AbstractTaskBackend, execution_ep_url: str) -> None:
        """
        Initialize the TaskManager with a specific backend.

        :param backend: An instance of AbstractTaskBackend.
        """
        self.task_registry = {}
        self.backend = backend
        self.execution_ep_url = execution_ep_url

    def task_exists(self, task_name: str) -> bool:
        """
        Check if a task with the given name exists in the registry.

        :param task_name: The name of the task to check.
        :return: True if the task exists, False otherwise.
        """
        return task_name in self.task_registry

    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        List all registered tasks.

        :return: A dictionary of task names and their corresponding RegisteredTask objects.
        """
        return [x for x in self.task_registry.values()]

    def stage_task(
        self, task_name: str, payload: Dict[str, Any], *args, **kwargs
    ) -> TaskExecution:
        """
        Send task to the backend / provider. The provider will trigger execution of the task (execute_task)
        """
        kwargs.setdefault("task_name", task_name)
        task_execution = TaskExecution.objects.create()
        task_execution.status = TaskExecutionState.PENDING
        task_execution.task_name = f"{task_name}_{task_execution.id}"
        task_execution.save()

        querystr = [
            f"{key}={value}" for key, value in kwargs.items() if value is not None
        ]
        execution_url = (
            f"{self.execution_ep_url}/{task_execution.id}/execute?{'&'.join(querystr)}"
        )

        response: TaskExeuctionCreateResponse = self.backend.create_http_task(
            target_url=execution_url,
            task_name=task_execution.task_name,
            payload=payload,
        )

        if response.success:
            task_execution.backend_task_id = response.task_id
            task_execution.status = response.status
            task_execution.save()
            return task_execution
        else:
            task_execution.status = TaskExecutionState.FAILED
            task_execution.result = "Failed to stage task execution"
            task_execution.save()

            raise Exception("Failed to stage task execution")

    def execute_task(self, task_id: int, *args, **kwargs) -> bool:
        """
        Execute a specific task.

        :param task_id: The ID of the task to execute.
        :return: True if the task was executed successfully, False otherwise.
        """
        task_callable = self.task_registry.get(task_id)
        if not task_callable:
            raise TaskNotFoundError(task_id)
        try:
            task_callable(*args, **kwargs)
            task_execution = TaskExecution.objects.get(id=task_id)
            task_execution.status = TaskExecutionState.COMPLETED
            task_execution.save()
            return True
        except Exception as e:
            task_execution = TaskExecution.objects.get(id=task_id)
            task_execution.status = TaskExecutionState.FAILED
            task_execution.result = str(e)
            task_execution.save()
            return False

    def get_task_status(self, task_id: int) -> TaskExecutionState:
        """
        Get the status of a specific task.

        :param task_id: The ID of the task to check.
        :return: TaskExecutionState object containing the status and details of the task.
        """
        task_execution = TaskExecution.objects.filter(id=task_id).first()
        if not task_execution:
            raise TaskNotFoundError(task_id)

        return self.backend.get_task_status(task_id=task_execution.backend_task_id)

    def cancel_task(self, task_id: int) -> bool:
        """
        Cancel a specific task.

        :param task_id: The ID of the task to cancel.
        :return: True if the task was canceled successfully, False otherwise.
        """
        return self.backend.cancel_task(task_id)


TASK_MANAGER = TaskManager(
    backend=GoogleCloudTaskBackend(
        queue_name=settings.GOOGLE_CLOUD_TASK_QUEUE_NAME,
        project_id=settings.GOOGLE_PROJECT_ID,
        location=settings.GOOGLE_PROJECT_LOCATION,
    ),
    execution_ep_url="http://localhost:8000/api/tasks/execute",
)


def task(
    name: str = "something_something",
    description: Optional[str] = None,
):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    if name in TASK_MANAGER.task_registry:
        raise ValueError(f"Task with name '{name}' is already registered.")

    TASK_MANAGER.task_registry[name] = RegisteredTask(
        callable=decorator,
        name=name,
        description=description,
    )

    return decorator
