# Generated by Django 3.1.1 on 2022-07-06 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0019_auto_20220704_1554'),
    ]

    operations = [
        migrations.AddField(
            model_name='planmanifest',
            name='timezone',
            field=models.CharField(default='UTC', max_length=124),
        ),
    ]