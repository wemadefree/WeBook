# Generated by Django 3.1.1 on 2023-10-27 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0095_auto_20231017_1137'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='title',
            field=models.CharField(blank=True, max_length=512, null=True, verbose_name='Title'),
        ),
    ]