# Generated by Django 3.1.1 on 2022-09-14 12:39

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0026_statustype'),
    ]

    operations = [
        migrations.AddField(
            model_name='statustype',
            name='color',
            field=colorfield.fields.ColorField(default='#FFFFFF', image_field=None, max_length=18, samples=None),
        ),
    ]