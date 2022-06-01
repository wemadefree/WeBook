# Generated by Django 3.1.1 on 2022-06-01 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0003_auto_20220518_0903'),
    ]

    operations = [
        migrations.AddField(
            model_name='arrangement',
            name='display_text',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Screen Display Text'),
        ),
        migrations.AddField(
            model_name='arrangement',
            name='display_text_en',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Screen Display Text(English)'),
        ),
        migrations.AlterField(
            model_name='arrangement',
            name='name_en',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Name(English)'),
        ),
    ]
