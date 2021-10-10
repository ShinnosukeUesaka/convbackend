# Generated by Django 3.1.6 on 2021-10-09 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0031_auto_20211009_1134'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='logitem',
            name='Scenario contraint',
        ),
        migrations.AlterField(
            model_name='logitem',
            name='corrected_text',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddConstraint(
            model_name='logitem',
            constraint=models.UniqueConstraint(fields=('log_number', 'scenario_first'), name='Scenario(first) contraint'),
        ),
        migrations.AddConstraint(
            model_name='logitem',
            constraint=models.UniqueConstraint(fields=('log_number', 'scenario_last'), name='Scenario(last) contraint'),
        ),
    ]
