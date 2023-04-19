# Generated by Django 3.1.1 on 2023-04-13 07:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0079_serviceorderchangeline_serviceorderchangesummary'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceorderchangesummary',
            name='service_order',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.RESTRICT, related_name='change_summaries', to='arrangement.serviceorder'),
            preserve_default=False,
        ),
    ]
