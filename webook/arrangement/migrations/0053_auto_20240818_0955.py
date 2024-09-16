# Generated by Django 3.2 on 2024-08-18 09:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('onlinebooking', '0018_auto_20240816_1230'),
        ('arrangement', '0052_auto_20231023_1339'),
    ]

    operations = [
        migrations.AddField(
            model_name='arrangement',
            name='booking_selected_audience',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='arrangement_booking_selected_audience', to='arrangement.audience', verbose_name='Selected Audience'),
        ),
        migrations.AddField(
            model_name='arrangement',
            name='city_segment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='arrangement_city_segment', to='onlinebooking.citysegment', verbose_name='City Segment'),
        ),
        migrations.AddField(
            model_name='arrangement',
            name='county',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='arrangement_county', to='onlinebooking.county', verbose_name='County'),
        ),
        migrations.AddField(
            model_name='arrangement',
            name='school',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='arrangement_school', to='onlinebooking.school', verbose_name='School'),
        ),
        migrations.AddField(
            model_name='event',
            name='booking_selected_audience',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='event_booking_selected_audience', to='arrangement.audience', verbose_name='Selected Audience'),
        ),
        migrations.AddField(
            model_name='event',
            name='city_segment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='event_city_segment', to='onlinebooking.citysegment', verbose_name='City Segment'),
        ),
        migrations.AddField(
            model_name='event',
            name='county',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='event_county', to='onlinebooking.county', verbose_name='County'),
        ),
        migrations.AddField(
            model_name='event',
            name='school',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='event_school', to='onlinebooking.school', verbose_name='School'),
        ),
    ]
