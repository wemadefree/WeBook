# Generated by Django 3.1.1 on 2023-06-22 10:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0087_auto_20230616_1338'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceorder',
            name='applied_preconfiguration',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='applied_to', to='arrangement.serviceorderpreconfiguration'),
        ),
        migrations.AlterField(
            model_name='service',
            name='resources',
            field=models.ManyToManyField(related_name='responsible_for_services', to='arrangement.Person'),
        ),
    ]