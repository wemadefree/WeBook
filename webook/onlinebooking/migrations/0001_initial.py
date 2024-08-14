# Generated by Django 3.2 on 2024-07-15 11:51

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('api', '0002_apiendpoint_disabled'),
        ('arrangement', '0052_auto_20231023_1339'),
    ]

    operations = [
        migrations.CreateModel(
            name='CitySegment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='County',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255)),
                ('city_segment_enabled', models.BooleanField(default=False)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255)),
                ('city_segment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schools_in_segment', to='onlinebooking.citysegment')),
                ('county', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schools_in_county', to='onlinebooking.county')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OnlineBookingSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allowed_audiences', models.ManyToManyField(to='arrangement.Audience')),
            ],
        ),
        migrations.CreateModel(
            name='OnlineBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField()),
                ('audience_type', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='arrangement.audience')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='onlinebooking.school')),
                ('segment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, to='onlinebooking.citysegment')),
                ('service_account', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='api.serviceaccount')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='citysegment',
            name='county',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='onlinebooking.county'),
        ),
    ]