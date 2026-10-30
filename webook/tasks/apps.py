from django.apps import AppConfig


class TaskConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "webook.tasks"

    def ready(self):
        # Import all files that start with "te_tasks" in the webook apps
        # This triggers the decorators, which will register the tasks in the manager.
        from django.conf import settings

        apps = settings.INSTALLED_APPS
        for app in apps:
            try:
                if not app.startswith("webook."):
                    continue

                path = ".".join(app.split(".")[0:2])
                _ = __import__(path, fromlist=["te_tasks"])
            except ImportError as e:
                continue

        return super().ready()
