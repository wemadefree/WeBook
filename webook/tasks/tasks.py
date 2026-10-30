from celery import shared_task


@shared_task
def execute_staged_task(task_execution_uuid: str):
    """Run a task staged through TASK_MANAGER, when TASK_BACKEND is "celery" """
    from .tasks_manager import TASK_MANAGER

    return TASK_MANAGER.run_staged_task(task_execution_uuid)
