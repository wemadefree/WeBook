# Generated by Django 3.1.1 on 2022-09-01 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrangement', '0021_arrangementtype_self_nested_children'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arrangementtype',
            name='self_nested_children',
            field=models.ManyToManyField(related_name='nested_parent', to='arrangement.ArrangementType'),
        ),
    ]
