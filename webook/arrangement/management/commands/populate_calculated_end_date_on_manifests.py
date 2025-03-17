"""populate_calculated_end_date_on_manifests.py

This module contains the populate_calculated_end_date_on_manifests command.
Populate the calculated_end_date field on all manifests in the database, to allow for calendar sync to make
filtering based on end date possible.
"""

from django.core.management.base import BaseCommand
from webook.arrangement.models import PlanManifest
from webook.utils.serie_calculator import calculate_serie


class Command(BaseCommand):
    help = "Populates the calculated_end_date field on all manifests in the database"

    def handle(self, *args, **options):
        for manifest in PlanManifest.objects.all():
            calculated_serie = calculate_serie(manifest)
            if not calculated_serie:
                self.stdout.write(
                    f"Could not calculate serie for manifest {manifest.id}"
                )
                continue
            manifest.calculated_end_date = calculated_serie[-1].date
            manifest.save()
            self.stdout.write(f"Updated manifest {manifest.id}")

        self.stdout.write(self.style.SUCCESS("Successfully updated all manifests"))
