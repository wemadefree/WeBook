# Generated by Django 3.1.1 on 2023-04-01 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0072_auto_20230329_2004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serviceorder',
            name='state',
            field=models.CharField(choices=[('awaiting', 'Awaiting'), ('denied', 'Denied'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('template', 'Template'), ('in_revision', 'In Revision')], default='awaiting', max_length=15),
        ),
    ]