# Generated by Django 3.1.1 on 2022-02-24 09:21

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import webook.arrangement.models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0039_confirmationreceipt_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonRequisition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('email', models.EmailField(max_length=254)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
            bases=(models.Model, webook.arrangement.models.ModelHistoricallyConfirmableMixin),
        ),
        migrations.CreateModel(
            name='ServiceRequisition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('order_information', models.TextField(blank=True)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
            bases=(models.Model, webook.arrangement.models.ModelHistoricallyConfirmableMixin),
        ),
        migrations.RemoveField(
            model_name='looseservicerequisition',
            name='ordered_service',
        ),
        migrations.RemoveField(
            model_name='requisitionrecord',
            name='associated_confirmation_receipt',
        ),
        migrations.DeleteModel(
            name='OrderedService',
        ),
        migrations.AddField(
            model_name='servicerequisition',
            name='originating_loose_requisition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='actual_requisition', to='arrangement.looseservicerequisition'),
        ),
        migrations.AddField(
            model_name='servicerequisition',
            name='provider',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='ordered_services', to='arrangement.serviceprovidable'),
        ),
        migrations.AddField(
            model_name='requisitionrecord',
            name='person_requisition',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='parent_record', to='arrangement.personrequisition'),
        ),
        migrations.AddField(
            model_name='requisitionrecord',
            name='service_requisition',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='parent_record', to='arrangement.servicerequisition'),
        ),
    ]