# Generated by Django 3.1.1 on 2023-01-31 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0060_auto_20230131_1202'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceorderprocessingrequest',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='serviceorderprocessingrequest',
            name='has_confirmed',
            field=models.BooleanField(default=False),
        ),
    ]
