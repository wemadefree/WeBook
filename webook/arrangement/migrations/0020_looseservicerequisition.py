# Generated by Django 3.1.1 on 2022-02-03 10:43

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0019_remove_event_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='LooseServiceRequisition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='arrangement.event', verbose_name='Event')),
                ('type_to_order', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='arrangement.servicetype', verbose_name='Type to order')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
    ]