from django.db import models
import uuid


class TaskExecutionState(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class TaskExecution(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    task_name = models.CharField(max_length=255)
    backend_task_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    status = models.CharField(
        max_length=50,
        choices=TaskExecutionState.choices,
        default=TaskExecutionState.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Task Execution"
        verbose_name_plural = "Task Executions"

    def __str__(self):
        return f"{self.task_name} - {self.status}"
