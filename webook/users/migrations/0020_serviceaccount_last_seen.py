# Generated by Django 3.2 on 2024-07-15 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_apiendpoint_serviceaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceaccount',
            name='last_seen',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
