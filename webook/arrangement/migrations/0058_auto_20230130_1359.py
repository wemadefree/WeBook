# Generated by Django 3.1.1 on 2023-01-30 12:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0057_auto_20230127_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceorder',
            name='assigned_personell',
            field=models.ManyToManyField(related_name='services_assigned_to', to='arrangement.Person'),
        ),
        migrations.AddField(
            model_name='serviceorder',
            name='freetext_comment',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='serviceorder',
            name='service',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.RESTRICT, related_name='associated_lines', to='arrangement.service'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='serviceorder',
            name='state',
            field=models.CharField(choices=[('awaiting', 'Awaiting'), ('denied', 'Denied'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('template', 'Template')], default='awaiting', max_length=10),
        ),
        migrations.AddField(
            model_name='serviceorder',
            name='template_for',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='arrangement.service'),
        ),
        migrations.DeleteModel(
            name='ServiceOrderLine',
        ),
    ]