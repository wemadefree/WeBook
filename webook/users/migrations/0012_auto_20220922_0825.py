# Generated by Django 3.1.1 on 2022-09-22 06:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_auto_20220920_1035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='timezone',
            field=models.CharField(default='UTC', max_length=255),
        ),
    ]