# Generated by Django 3.1.1 on 2022-02-21 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0029_auto_20220221_0826'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='silo',
            field=models.CharField(choices=[('planning_silo', 'planning_silo'), ('production_silo', 'production_silo')], default='planning_silo', max_length=255),
        ),
    ]