# Generated by Django 3.1.1 on 2022-09-19 07:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0029_arrangement_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='planmanifest',
            name='status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='manifests_of_status', to='arrangement.statustype'),
        ),
    ]
