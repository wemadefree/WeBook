# Generated by Django 3.1.1 on 2022-03-03 07:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0042_requisitionrecord_arrangement'),
    ]

    operations = [
        migrations.AddField(
            model_name='personrequisition',
            name='confirmation_receipt',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.RESTRICT, related_name='person_requisition', to='arrangement.confirmationreceipt'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='personrequisition',
            name='historic_confirmation_receipts',
            field=models.ManyToManyField(to='arrangement.ConfirmationReceipt'),
        ),
        migrations.AddField(
            model_name='servicerequisition',
            name='confirmation_receipt',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.RESTRICT, related_name='service_requisition', to='arrangement.confirmationreceipt'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='servicerequisition',
            name='historic_confirmation_receipts',
            field=models.ManyToManyField(to='arrangement.ConfirmationReceipt'),
        ),
    ]