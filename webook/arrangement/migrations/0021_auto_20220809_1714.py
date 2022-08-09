# Generated by Django 3.1.1 on 2022-08-09 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0020_planmanifest_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arrangement',
            name='actual_visitors',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='Actual visitors'),
        ),
        migrations.AlterField(
            model_name='event',
            name='actual_visitors',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='Actual visitors'),
        ),
    ]