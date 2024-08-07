# Generated by Django 3.1.1 on 2022-10-04 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0038_auto_20220927_1212'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='after_buffer_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='after_buffer_title',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='before_buffer_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='before_buffer_title',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='after_buffer_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='after_buffer_title',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='before_buffer_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='before_buffer_title',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
