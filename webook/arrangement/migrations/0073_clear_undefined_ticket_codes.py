from django.db import migrations


def clear_undefined_ticket_codes(apps, schema_editor):
    """Series created in the planner stored the string "undefined" as ticket code (typo in
    serieConvert.js from 2022-11 until 2026-10). Clear it on the plan manifests and their events."""
    PlanManifest = apps.get_model("arrangement", "PlanManifest")
    Event = apps.get_model("arrangement", "Event")

    PlanManifest.objects.filter(ticket_code="undefined").update(ticket_code="")
    Event.objects.filter(ticket_code="undefined").update(ticket_code=None)


class Migration(migrations.Migration):

    dependencies = [
        ("arrangement", "0072_alter_serviceorderchangeline_provision_and_more"),
    ]

    operations = [
        migrations.RunPython(clear_undefined_ticket_codes, migrations.RunPython.noop),
    ]
