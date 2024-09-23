# Generated by Django 3.2 on 2024-08-20 12:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('onlinebooking', '0018_auto_20240816_1230'),
        ('arrangement', '0054_auto_20240818_1052'),
    ]

    operations = [
        migrations.AddField(
            model_name='planmanifest',
            name='booking_selected_audience',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='planmanifest_booking_selected_audience', to='arrangement.audience', verbose_name='Selected Audience'),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='city_segment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='planmanifest_city_segment', to='onlinebooking.citysegment', verbose_name='City Segment'),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='county',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='planmanifest_county', to='onlinebooking.county', verbose_name='County'),
        ),
        migrations.AddField(
            model_name='planmanifest',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='planmanifest_school', to='onlinebooking.school', verbose_name='School'),
        ),
    ]