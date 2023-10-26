# Generated by Django 3.1.1 on 2023-01-25 07:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0054_serviceorder_serviceordermailing'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceorder',
            name='ordered_for_event',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='arrangement.event'),
            preserve_default=False,
        ),
    ]