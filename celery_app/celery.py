import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
app = Celery("webook")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(packages=["webook.celery_haystack", "webook.tasks"])

app.conf.result_backend = "django-db"
app.conf.timezone = "Europe/Oslo"


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    pass


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
