# Generated by Django 3.1.1 on 2022-06-30 06:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0015_auto_20220629_1324'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventseriefile',
            options={},
        ),
        migrations.RenameField(
            model_name='eventseriefile',
            old_name='event_serie',
            new_name='associated_with',
        ),
        migrations.AlterField(
            model_name='eventfile',
            name='file',
            field=models.FileField(upload_to='uploadedFiles/'),
        ),
        migrations.AlterField(
            model_name='eventseriefile',
            name='file',
            field=models.FileField(upload_to='uploadedFiles/'),
        ),
        migrations.AlterField(
            model_name='eventseriefile',
            name='uploader',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='files_uploaded_to_eventseriefile', to='arrangement.person'),
        ),
    ]
