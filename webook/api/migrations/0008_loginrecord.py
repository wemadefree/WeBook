# Generated by Django 4.2.10 on 2025-01-31 13:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_serviceaccount_service_account_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoginRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('login_time', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField()),
                ('service_account', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='login_records', to='api.serviceaccount')),
            ],
            options={
                'verbose_name': 'Login Record',
                'verbose_name_plural': 'Login Records',
            },
        ),
    ]
