# Generated by Django 3.1.6 on 2021-10-05 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0025_auto_20211002_1135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='phrases',
            field=models.TextField(blank=True, default='[]', max_length=10000, null=True),
        ),
    ]
