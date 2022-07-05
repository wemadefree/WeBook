# Generated by Django 3.1.1 on 2022-07-04 15:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0018_auto_20220704_1447'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='buffer_after_event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='after_buffer_for', to='arrangement.event'),
        ),
        migrations.AddField(
            model_name='event',
            name='buffer_before_event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='before_buffer_for', to='arrangement.event'),
        ),
    ]
