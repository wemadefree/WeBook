# Generated by Django 3.1.1 on 2023-03-20 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0066_auto_20230310_1247'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceorderprovision',
            name='comment_to_personell',
            field=models.TextField(blank=True),
        ),
    ]