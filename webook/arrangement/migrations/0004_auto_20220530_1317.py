# Generated by Django 3.1.1 on 2022-05-30 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0003_auto_20220518_0903'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='silo',
            field=models.CharField(choices=[('production_silo', 'production_silo'), ('collision_silo', 'collision_silo')], default='production_silo', max_length=255),
        ),
    ]