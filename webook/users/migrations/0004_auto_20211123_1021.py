# Generated by Django 3.1.1 on 2021-11-23 09:21

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20211123_1004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='slug',
            field=autoslug.fields.AutoSlugField(blank=True, editable=False, populate_from='_get_slug', unique=True),
        ),
    ]
