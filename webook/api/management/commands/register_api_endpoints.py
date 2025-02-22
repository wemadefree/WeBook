import os
from typing import Dict, Set
import django
from django.core.management.base import BaseCommand
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = "Register API endpoints in the database"

    ignored_endpoints: Set[str] = {
        "api-root",
        "openapi-json",
        "openapi-view",
        "login_service_account",
    }

    def handle(self, *args, **kwargs):
        try:
            initial_migration = MigrationRecorder.Migration.objects.filter(
                app="api", name="0001_initial"
            )
            if not initial_migration:
                print(
                    "API models not migrated yet, will not proceed with registering endpoints, please run migrations before starting the server"
                )

            print("Registering API Endpoints")
            from webook.api.api import api
            from webook.api.models import APIScope

            original_value = os.getenv("NINJA_SKIP_REGISTRY", "0")
            os.environ["NINJA_SKIP_REGISTRY"] = "1"

            registered_endpoints = APIScope.objects.filter(disabled=False)
            registered_endpoints_url_map = {
                x.operation_id: x.path for x in registered_endpoints
            }
            registered_operation_ids = set(
                registered_endpoints.values_list("operation_id", flat=True)
            )
            # calling urls triggers __validation, which registers endpoints.
            # this will cause an error to be raised when the api is initialized
            # we avoid this with the NINJA_SKIP_REGISTRY environment variable
            present_urls_lookup: Dict[str, str] = {
                x.name: x.pattern._route
                for x in api.urls[0]
                if x.name not in self.ignored_endpoints
            }
            present_urls_opset = set(present_urls_lookup.keys())

            os.environ["NINJA_SKIP_REGISTRY"] = original_value

            new = set(present_urls_opset - registered_operation_ids)
            to_delete = registered_operation_ids - present_urls_opset
            intersect = registered_operation_ids.intersection(present_urls_opset)

            if not new and not to_delete and not intersect:
                print("No changes in API Endpoints")
                return

            for operation_id in to_delete:
                ep = APIScope.objects.get(operation_id=operation_id)
                ep.disabled = True
                ep.save()
                print(f"Disabled {operation_id}")

            for operation_id in new:
                try:
                    existing = APIScope.objects.get(operation_id=operation_id)
                except APIScope.DoesNotExist:
                    existing = None

                if existing:
                    existing.disabled = False
                    existing.save()
                    print(f"Enabled {operation_id}")
                    continue

                api_endpoint = APIScope(
                    operation_id=operation_id, path=present_urls_lookup[operation_id]
                )
                api_endpoint.save()
                print(f"Registered {operation_id}")

            for operation_id in intersect:
                if (
                    present_urls_lookup[operation_id]
                    != registered_endpoints_url_map[operation_id]
                ):
                    ep = APIScope.objects.get(operation_id=operation_id)
                    ep.path = present_urls_lookup[operation_id]
                    ep.save()
                    print(f"Updated {operation_id}")
        except django.db.utils.ProgrammingError:
            print("Database not ready, skipping API endpoint registration")
