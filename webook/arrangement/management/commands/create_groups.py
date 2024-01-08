"""create_groups.py

This module contains the create_groups command. This command should be used when initially setting up the application with an empty
database. The command will populate the database with the groups that are used in the application.
"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Populates the database with required groups"

    __groups = ["readonly_level_2", "readonly", "planners"]

    def handle(self, *args, **options):
        for group in self.__groups:
            Group.objects.get_or_create(name=group)
            self.stdout.write(f"Created group {group}")

        self.stdout.write(self.style.SUCCESS("Successfully created all groups"))
