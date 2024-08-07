# Generated by Django 3.1.1 on 2022-09-27 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0036_planmanifest_responsible'),
    ]

    operations = [
        migrations.AddField(
            model_name='arrangement',
            name='display_text',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Screen Display Text'),
        ),
        migrations.AddField(
            model_name='arrangement',
            name='display_text_en',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Screen Display Text(English)'),
        ),
    ]
