# Generated by Django 4.2.10 on 2024-12-19 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('graph_integration', '0002_syncedevent_event_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='graphcalendar',
            name='last_synced_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
                model_name='graphcalendar',
            name='subscribed_at',
            field=models.DateTimeField(auto_now_add=True, default=None),
            preserve_default=False,
        ),
    ]
