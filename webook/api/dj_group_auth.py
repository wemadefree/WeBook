import logging
from typing import Any, Optional
from django.http import HttpRequest
from ninja.security.apikey import APIKeyCookie
from django.contrib.auth.models import Group


class SessionGroupAuth(APIKeyCookie):
    _known_groups = {}

    def __init__(self, group_name: str):
        self.group_name = group_name
        self.param_name = f"{group_name}_session"

        if not self.group_name:
            raise ValueError("group_name must be provided")

        super().__init__()

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[Any]:
        # Checked on first use rather than in __init__, as routers are instantiated
        # at import time, before the database is guaranteed to be migrated.
        if self.group_name not in self._known_groups:
            if not Group.objects.filter(name=self.group_name).exists():
                logging.error(
                    f"Group {self.group_name} does not exist; only superusers will be authorized."
                )
            self._known_groups[self.group_name] = True

        if request.user.is_authenticated and (
            request.user.groups.filter(name=self.group_name).exists()
            or request.user.is_superuser
        ):
            return request.user

        return None
