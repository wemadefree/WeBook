# Generated by Django 3.1.1 on 2022-09-20 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_merge_20220919_0927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='timezone',
            field=models.CharField(default='Europe/Oslo', max_length=255),
        ),
    ]
