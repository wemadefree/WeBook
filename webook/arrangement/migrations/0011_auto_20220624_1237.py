# Generated by Django 3.1.1 on 2022-06-24 10:37

import autoslug.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0010_auto_20220614_1230'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arrangement',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='arrangementtype',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='audience',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='people',
            field=models.ManyToManyField(blank=True, related_name='my_events', to='arrangement.Person', verbose_name='People'),
        ),
        migrations.AlterField(
            model_name='event',
            name='rooms',
            field=models.ManyToManyField(blank=True, to='arrangement.Room', verbose_name='Rooms'),
        ),
        migrations.AlterField(
            model_name='location',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='organizationtype',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='full_name', unique=True),
        ),
        migrations.AlterField(
            model_name='room',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='roompreset',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
        migrations.AlterField(
            model_name='servicetype',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, manager_name='all_objects', populate_from='name', unique=True),
        ),
    ]
