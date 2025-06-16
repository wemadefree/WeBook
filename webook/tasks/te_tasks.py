from .tasks_manager import task


@task(name="test_task", description="A simple test task that does nothing")
def test_task():
    """
    A simple test task that does nothing.
    This is used to demonstrate the task management system.
    """
    print("Test task executed successfully.")
    return True
