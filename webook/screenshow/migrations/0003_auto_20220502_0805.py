# Generated by Django 3.1.1 on 2022-05-02 06:05

import autoslug.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0057_room_has_screen'),
        ('screenshow', '0002_auto_20220419_0219'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='displaylayout',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='screenresource',
            name='is_room_screen',
        ),
        migrations.RemoveField(
            model_name='screenresource',
            name='name',
        ),
        migrations.RemoveField(
            model_name='screenresource',
            name='name_en',
        ),
        migrations.RemoveField(
            model_name='screenresource',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='screenresource',
            name='screen_groups',
        ),
        migrations.AddField(
            model_name='displaylayout',
            name='items_shown',
            field=models.IntegerField(default=10, verbose_name='Items Shown'),
        ),
        migrations.AddField(
            model_name='screengroup',
            name='room_preset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='arrangement.roompreset', verbose_name='Room Preset'),
        ),
        migrations.AddField(
            model_name='screenresource',
            name='folder_path',
            field=models.CharField(max_length=255, null=True, verbose_name='Folder Path'),
        ),
        migrations.AddField(
            model_name='screenresource',
            name='generated_name',
            field=models.CharField(max_length=255, null=True, verbose_name='Generated Name'),
        ),
        migrations.AddField(
            model_name='screenresource',
            name='items_shown',
            field=models.IntegerField(default=10, verbose_name='Shown Items'),
        ),
        migrations.AddField(
            model_name='screenresource',
            name='room',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='arrangement.room', verbose_name='Room Based'),
        ),
        migrations.AddField(
            model_name='screenresource',
            name='screen_model',
            field=models.CharField(default=None, max_length=255, verbose_name='Screen Model'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='screenresource',
            name='status',
            field=models.IntegerField(choices=[(0, 'Available'), (1, 'Unavailable')], default=0, verbose_name='Screen Status'),
        ),
        migrations.AlterField(
            model_name='displaylayout',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Layout Enabled'),
        ),
        migrations.AlterField(
            model_name='screenresource',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, populate_from='screen_model', unique=True),
        ),
    ]
