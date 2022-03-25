# Generated by Django 3.1.1 on 2022-03-25 10:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0046_arrangement_arrangement_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='arrangement',
            name='location',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='arrangements', to='arrangement.location', verbose_name='Location'),
            preserve_default=False,
        ),
    ]
