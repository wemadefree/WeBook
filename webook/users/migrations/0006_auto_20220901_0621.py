# Generated by Django 3.1.1 on 2022-09-01 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20220810_1337'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='timezone',
            field=models.CharField(default='Europe/Oslo', max_length=255),
        ),
    ]
