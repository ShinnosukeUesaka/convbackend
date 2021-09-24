# Generated by Django 3.1.6 on 2021-09-24 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0021_scenario_expressions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='category',
            field=models.CharField(default='Role Play', max_length=100),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='expressions',
            field=models.TextField(blank=True, default='', max_length=10000, null=True),
        ),
    ]
