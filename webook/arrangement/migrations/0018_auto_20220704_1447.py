# Generated by Django 3.1.1 on 2022-07-04 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0017_auto_20220630_0745'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='after_buffer_end',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='after_buffer_start',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='before_buffer_end',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='before_buffer_start',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='after_buffer_end',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='after_buffer_start',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='before_buffer_end',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='before_buffer_start',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
