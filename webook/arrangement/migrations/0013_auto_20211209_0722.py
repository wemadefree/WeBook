# Generated by Django 3.1.1 on 2021-12-09 07:22

import autoslug.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0012_merge_20211130_0931'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='max_capacity',
            field=models.IntegerField(default=0, verbose_name='Maximum Occupants'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='arrangement',
            name='audience',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='arrangements', to='arrangement.audience', verbose_name='Audience'),
        ),
        migrations.AlterField(
            model_name='arrangement',
            name='organization_participants',
            field=models.ManyToManyField(related_name='participating_in', to='arrangement.Organization', verbose_name='Organization Participants'),
        ),
        migrations.AlterField(
            model_name='arrangement',
            name='owners',
            field=models.ManyToManyField(to='arrangement.Person', verbose_name='Owners'),
        ),
        migrations.AlterField(
            model_name='arrangement',
            name='people_participants',
            field=models.ManyToManyField(related_name='participating_in', to='arrangement.Person', verbose_name='People Participants'),
        ),
        migrations.AlterField(
            model_name='arrangement',
            name='timeline_events',
            field=models.ManyToManyField(to='arrangement.TimelineEvent', verbose_name='Timeline Events'),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='owners', to='arrangement.person', verbose_name='Owner'),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='people_resources',
            field=models.ManyToManyField(to='arrangement.Person', verbose_name='People Resources'),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='room_resources',
            field=models.ManyToManyField(to='arrangement.Room', verbose_name='Room Resources'),
        ),
        migrations.AlterField(
            model_name='confirmationreceipt',
            name='requested_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='arrangement.person', verbose_name='Requested By'),
        ),
        migrations.AlterField(
            model_name='event',
            name='arrangement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='arrangement.arrangement', verbose_name='Arrangement'),
        ),
        migrations.AlterField(
            model_name='event',
            name='articles',
            field=models.ManyToManyField(to='arrangement.Article', verbose_name='Articles'),
        ),
        migrations.AlterField(
            model_name='event',
            name='notes',
            field=models.ManyToManyField(to='arrangement.Note', verbose_name='Notes'),
        ),
        migrations.AlterField(
            model_name='event',
            name='people',
            field=models.ManyToManyField(to='arrangement.Person', verbose_name='People'),
        ),
        migrations.AlterField(
            model_name='event',
            name='rooms',
            field=models.ManyToManyField(to='arrangement.Room', verbose_name='Rooms'),
        ),
        migrations.AlterField(
            model_name='eventservice',
            name='associated_people',
            field=models.ManyToManyField(to='arrangement.Person', verbose_name='Associated People'),
        ),
        migrations.AlterField(
            model_name='eventservice',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='arrangement.event', verbose_name='Event'),
        ),
        migrations.AlterField(
            model_name='eventservice',
            name='notes',
            field=models.ManyToManyField(to='arrangement.Note', verbose_name='Notes'),
        ),
        migrations.AlterField(
            model_name='eventservice',
            name='receipt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='arrangement.confirmationreceipt', verbose_name='Receipt'),
        ),
        migrations.AlterField(
            model_name='eventservice',
            name='service_provider',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='arrangement.serviceprovider', verbose_name='Service Provider'),
        ),
        migrations.AlterField(
            model_name='note',
            name='confirmation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, to='arrangement.confirmationreceipt', verbose_name='Confirmation Receipt'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='members',
            field=models.ManyToManyField(related_name='organizations', to='arrangement.Person', verbose_name='Members'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='notes',
            field=models.ManyToManyField(to='arrangement.Note', verbose_name='Notes'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='organization_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='organizations', to='arrangement.organizationtype', verbose_name='Organization Type'),
        ),
        migrations.AlterField(
            model_name='person',
            name='birth_date',
            field=models.DateField(blank=True, null=True, verbose_name='Birth Date'),
        ),
        migrations.AlterField(
            model_name='person',
            name='business_hours',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='arrangement.businesshour', verbose_name='Business Hours'),
        ),
        migrations.AlterField(
            model_name='person',
            name='first_name',
            field=models.CharField(max_length=255, verbose_name='First Name'),
        ),
        migrations.AlterField(
            model_name='person',
            name='last_name',
            field=models.CharField(max_length=255, verbose_name='Last Name'),
        ),
        migrations.AlterField(
            model_name='person',
            name='middle_name',
            field=models.CharField(blank=True, max_length=255, verbose_name='Middle Name'),
        ),
        migrations.AlterField(
            model_name='person',
            name='notes',
            field=models.ManyToManyField(to='arrangement.Note', verbose_name='Notes'),
        ),
        migrations.AlterField(
            model_name='person',
            name='personal_email',
            field=models.CharField(max_length=255, verbose_name='Personal Email'),
        ),
        migrations.AlterField(
            model_name='person',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, populate_from='full_name', unique=True),
        ),
        migrations.AlterField(
            model_name='room',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rooms', to='arrangement.location', verbose_name='Location'),
        ),
        migrations.AlterField(
            model_name='serviceprovider',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='arrangement.organization', verbose_name='Organization'),
        ),
        migrations.AlterField(
            model_name='serviceprovider',
            name='service_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='arrangement.servicetype', verbose_name='Service Type'),
        ),
    ]