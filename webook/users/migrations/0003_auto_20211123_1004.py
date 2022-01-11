# Generated by Django 3.1.1 on 2021-11-23 09:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0010_timelineevent_stamp'),
        ('users', '0002_auto_20211123_0957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='person',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='arrangement.person'),
        ),
    ]