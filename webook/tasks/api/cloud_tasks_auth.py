import logging
from typing import Optional

from django.conf import settings
from django.http import HttpRequest
from ninja.security import HttpBearer


class CloudTasksOIDCAuth(HttpBearer):
    """
    Authenticates requests from Google Cloud Tasks, by verifying the OIDC token it sends for the
    configured service account (GOOGLE_CLOUD_TASK_SERVICE_ACCOUNT).

    Rejects every request unless TASK_BACKEND is "google_cloud"; the other backends run tasks
    without going through HTTP.
    """

    def authenticate(self, request: HttpRequest, token: str) -> Optional[str]:
        service_account = settings.GOOGLE_CLOUD_TASK_SERVICE_ACCOUNT
        if settings.TASK_BACKEND != "google_cloud" or not service_account:
            return None

        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token

        try:
            claims = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                audience=settings.GOOGLE_CLOUD_TASK_OIDC_AUDIENCE,
            )
        except ValueError as e:
            logging.warning(f"Rejected task execution request with invalid token: {e}")
            return None

        if claims.get("email") != service_account or not claims.get("email_verified"):
            logging.warning(
                f"Rejected task execution request from {claims.get('email')}"
            )
            return None

        return claims["email"]
