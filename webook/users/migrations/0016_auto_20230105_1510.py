# Generated by Django 3.1.1 on 2023-01-05 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_merge_20221212_2116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='timezone',
            field=models.CharField(default='Europe/Oslo', max_length=255),
        ),
    ]
