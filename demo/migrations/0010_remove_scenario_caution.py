# Generated by Django 3.1.6 on 2021-08-23 07:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0009_auto_20210823_0702'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scenario',
            name='caution',
        ),
    ]
