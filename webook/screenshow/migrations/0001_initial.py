# Generated by Django 3.1.1 on 2022-05-11 11:42

import autoslug.fields
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('arrangement', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisplayLayoutSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('html_template', models.TextField(verbose_name='HTML Template')),
                ('css_template', models.TextField(verbose_name='CSS Template')),
                ('file_output_path', models.TextField(blank=True, max_length=255, verbose_name='File Output Path')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='name', unique=True)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ScreenResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('screen_model', models.CharField(max_length=255, verbose_name='Screen Model')),
                ('items_shown', models.IntegerField(default=10, verbose_name='Shown Items')),
                ('status', models.IntegerField(choices=[(0, 'Available'), (1, 'Unavailable')], default=0, verbose_name='Screen Status')),
                ('folder_path', models.CharField(max_length=255, null=True, verbose_name='Folder Path')),
                ('generated_name', models.CharField(max_length=255, null=True, verbose_name='Generated Name')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='screen_model', unique=True)),
                ('room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='arrangement.room', verbose_name='Room Based')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ScreenGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('group_name', models.CharField(max_length=255, verbose_name='Group Name')),
                ('group_name_en', models.CharField(max_length=255, null=True, verbose_name='Screen Group Name English')),
                ('quantity', models.IntegerField(default=10, verbose_name='Quantity')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='group_name', unique=True)),
                ('room_preset', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='arrangement.roompreset', verbose_name='Room Preset')),
                ('screens', models.ManyToManyField(to='screenshow.ScreenResource', verbose_name='Screen Resources')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DisplayLayout',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='Description')),
                ('items_shown', models.IntegerField(default=10, verbose_name='Items Shown')),
                ('is_room_based', models.BooleanField(default=True, verbose_name='Is Room Based')),
                ('all_events', models.BooleanField(default=True, verbose_name='All Events')),
                ('is_active', models.BooleanField(default=True, verbose_name='Layout Enabled')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='name', unique=True)),
                ('groups', models.ManyToManyField(related_name='layouts', to='screenshow.ScreenGroup', verbose_name='Screen Groups')),
                ('screens', models.ManyToManyField(related_name='layouts', to='screenshow.ScreenResource', verbose_name='Screen Resources')),
                ('setting', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='screenshow.displaylayoutsetting', verbose_name='Display Layout Setting')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
    ]
