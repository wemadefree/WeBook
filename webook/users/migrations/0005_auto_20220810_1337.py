# Generated by Django 3.1.1 on 2022-08-10 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20220809_1714'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='timezone',
            field=models.CharField(default='UTC', max_length=255),
        ),
    ]
