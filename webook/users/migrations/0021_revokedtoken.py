# Generated by Django 3.2 on 2024-07-15 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_serviceaccount_last_seen'),
    ]

    operations = [
        migrations.CreateModel(
            name='RevokedToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=255, unique=True)),
                ('revoked_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
