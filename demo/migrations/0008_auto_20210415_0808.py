# Generated by Django 3.1.6 on 2021-04-15 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0007_auto_20210415_0801'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='logitem',
            constraint=models.UniqueConstraint(fields=('log_number', 'scenario'), name='Scenario contraint'),
        ),
    ]
