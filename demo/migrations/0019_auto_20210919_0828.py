# Generated by Django 3.1.6 on 2021-09-19 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0018_remove_scenario_controller_variables'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='duration',
            field=models.IntegerField(default='3'),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='level',
            field=models.IntegerField(default='2'),
        ),
    ]
