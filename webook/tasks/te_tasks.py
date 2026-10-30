from .tasks_manager import task


@task(name="test_task", description="A simple test task that does nothing")
def test_task(value: str = "default") -> dict:
    """
    A simple test task that does nothing.
    This is used to demonstrate the task management system.
    """
    print("Test task executed successfully.")
    return {"status": "success", "value": value}
