# Generated by Django 3.1.1 on 2023-06-30 06:42

from django.db import migrations, models
import django.db.models.deletion
import django.views.generic.detail


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0091_merge_20230630_0842'),
    ]

    operations = [
        migrations.CreateModel(
            name='GetServicePersonellJsonView',
            fields=[
                ('service_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='arrangement.service')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
            bases=('arrangement.service', django.views.generic.detail.DetailView),
        ),
        migrations.AlterField(
            model_name='serviceorderpreconfiguration',
            name='assigned_personell',
            field=models.ManyToManyField(blank=True, related_name='associated_with_preconfigurations', to='arrangement.Person'),
        ),
    ]