# Generated by Django 3.1.1 on 2022-06-13 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0007_auto_20220610_1526'),
    ]

    operations = [
        migrations.AddField(
            model_name='arrangement',
            name='meeting_place_en',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Meeting Place (English)'),
        ),
    ]
