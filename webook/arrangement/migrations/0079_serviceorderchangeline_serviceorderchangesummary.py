# Generated by Django 3.1.1 on 2023-04-13 07:18

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0078_auto_20230413_0859'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceOrderChangeSummary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('is_archived', models.BooleanField(default=False, verbose_name='Is archived')),
                ('archived_when', models.DateTimeField(null=True, verbose_name='Archived when')),
                ('type', models.CharField(choices=[('serie', 'Serie'), ('event', 'Event')], default='serie', max_length=10)),
                ('archived_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='serviceorderchangesummary_archived_by', to='arrangement.person', verbose_name='Archived by')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceOrderChangeLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('is_archived', models.BooleanField(default=False, verbose_name='Is archived')),
                ('archived_when', models.DateTimeField(null=True, verbose_name='Archived when')),
                ('date', models.DateField(verbose_name='Date')),
                ('type_of_change', models.CharField(choices=[('new', 'New'), ('times_changed', 'Times Changed'), ('removed', 'Removed')], default='new', max_length=15)),
                ('archived_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='serviceorderchangeline_archived_by', to='arrangement.person', verbose_name='Archived by')),
                ('summary', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='lines', to='arrangement.serviceorderchangesummary')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
    ]