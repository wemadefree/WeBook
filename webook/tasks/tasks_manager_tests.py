import time
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from django.test import TestCase, override_settings

from webook.tasks.api.cloud_tasks_auth import CloudTasksOIDCAuth
from webook.tasks.models import TaskExecution, TaskExecutionState
from webook.tasks.tasks_manager import TASK_MANAGER, CeleryTaskBackend

SERVICE_ACCOUNT = "tasks@example.iam.gserviceaccount.com"


def stage_test_task(status=TaskExecutionState.PENDING) -> TaskExecution:
    return TaskExecution.objects.create(
        task_name="test_task", parameters={"value": "hello"}, status=status
    )


class RunStagedTaskTests(TestCase):
    def test_runs_pending_task(self):
        task_execution = stage_test_task()

        self.assertTrue(TASK_MANAGER.run_staged_task(task_execution.uuid))

        task_execution.refresh_from_db()
        self.assertEqual(task_execution.status, TaskExecutionState.COMPLETED)
        self.assertIn("hello", task_execution.result)
        self.assertIsNotNone(task_execution.completed_at)

    def test_does_not_run_completed_or_running_task_again(self):
        for status in (TaskExecutionState.COMPLETED, TaskExecutionState.RUNNING):
            task_execution = stage_test_task(status=status)

            with patch.object(TASK_MANAGER, "execute_task") as execute_task:
                self.assertIsNone(TASK_MANAGER.run_staged_task(task_execution.uuid))
                execute_task.assert_not_called()

    def test_retries_failed_task(self):
        task_execution = stage_test_task(status=TaskExecutionState.FAILED)

        self.assertTrue(TASK_MANAGER.run_staged_task(task_execution.uuid))

    def test_unknown_task_raises(self):
        with self.assertRaises(TaskExecution.DoesNotExist):
            TASK_MANAGER.run_staged_task(uuid.uuid4())


class CeleryTaskBackendTests(TestCase):
    def test_sends_task_after_commit(self):
        task_execution = stage_test_task()

        with patch("webook.tasks.tasks.execute_staged_task.apply_async") as apply_async:
            with self.captureOnCommitCallbacks(execute=True):
                response = CeleryTaskBackend().create_http_task(
                    target_url="unused", task_execution_uuid=task_execution.uuid
                )
                apply_async.assert_not_called()

        apply_async.assert_called_once_with(
            args=[str(task_execution.uuid)],
            task_id=response.task_id,
            countdown=None,
        )


@override_settings(GOOGLE_CLOUD_TASKS_EMULATOR_OIDC_ISSUER=None)
class CloudTasksOIDCAuthTests(TestCase):
    """Tokens issued by Google (no emulator configured)"""

    def authenticate(self, claims=None, error=None):
        with patch("google.oauth2.id_token.verify_oauth2_token") as verify:
            verify.return_value = claims
            verify.side_effect = error
            return CloudTasksOIDCAuth().authenticate(request=None, token="token")

    @override_settings(TASK_BACKEND="celery", GOOGLE_CLOUD_TASK_SERVICE_ACCOUNT=SERVICE_ACCOUNT)
    def test_rejects_when_not_using_cloud_tasks(self):
        claims = {"email": SERVICE_ACCOUNT, "email_verified": True}
        self.assertIsNone(self.authenticate(claims))

    @override_settings(TASK_BACKEND="google_cloud", GOOGLE_CLOUD_TASK_SERVICE_ACCOUNT=None)
    def test_rejects_without_configured_service_account(self):
        claims = {"email": SERVICE_ACCOUNT, "email_verified": True}
        self.assertIsNone(self.authenticate(claims))

    @override_settings(TASK_BACKEND="google_cloud", GOOGLE_CLOUD_TASK_SERVICE_ACCOUNT=SERVICE_ACCOUNT)
    def test_accepts_token_for_service_account(self):
        claims = {"email": SERVICE_ACCOUNT, "email_verified": True}
        self.assertEqual(self.authenticate(claims), SERVICE_ACCOUNT)

    @override_settings(TASK_BACKEND="google_cloud", GOOGLE_CLOUD_TASK_SERVICE_ACCOUNT=SERVICE_ACCOUNT)
    def test_rejects_other_account_or_invalid_token(self):
        self.assertIsNone(
            self.authenticate({"email": "someone@example.com", "email_verified": True})
        )
        self.assertIsNone(self.authenticate(error=ValueError("bad token")))


EMULATOR_ISSUER = "http://cloud-tasks-emulator:8980"
EMULATOR_AUDIENCE = "http://webook:8080"


@override_settings(
    TASK_BACKEND="google_cloud",
    GOOGLE_CLOUD_TASK_SERVICE_ACCOUNT=SERVICE_ACCOUNT,
    GOOGLE_CLOUD_TASKS_EMULATOR_OIDC_ISSUER=EMULATOR_ISSUER,
    GOOGLE_CLOUD_TASK_OIDC_AUDIENCE=EMULATOR_AUDIENCE,
)
class CloudTasksEmulatorTokenTests(TestCase):
    def setUp(self):
        self.emulator_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def token(self, signing_key=None, **claims):
        payload = {
            "iss": EMULATOR_ISSUER,
            "aud": EMULATOR_AUDIENCE,
            "email": SERVICE_ACCOUNT,
            "email_verified": True,
            "exp": int(time.time()) + 300,
            **claims,
        }
        return jwt.encode(payload, signing_key or self.emulator_key, algorithm="RS256")

    def authenticate(self, token):
        # Stands in for fetching the emulator's /jwks
        published_key = SimpleNamespace(key=self.emulator_key.public_key())
        with patch("jwt.PyJWKClient.get_signing_key_from_jwt", return_value=published_key):
            return CloudTasksOIDCAuth().authenticate(request=None, token=token)

    def test_accepts_emulator_token(self):
        self.assertEqual(self.authenticate(self.token()), SERVICE_ACCOUNT)

    def test_rejects_wrong_issuer_audience_or_key(self):
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        self.assertIsNone(self.authenticate(self.token(iss="http://elsewhere")))
        self.assertIsNone(self.authenticate(self.token(aud="http://other-app")))
        self.assertIsNone(self.authenticate(self.token(signing_key=other_key)))


class ExecuteTaskEndpointTests(TestCase):
    def test_rejects_request_without_token(self):
        task_execution = stage_test_task()

        response = self.client.post(
            f"/api/tasks/execute-task?task_uuid={task_execution.uuid}"
        )

        self.assertEqual(response.status_code, 401)
        task_execution.refresh_from_db()
        self.assertEqual(task_execution.status, TaskExecutionState.PENDING)
