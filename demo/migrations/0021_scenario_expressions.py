# Generated by Django 3.1.6 on 2021-09-24 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0020_auto_20210921_1111'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='expressions',
            field=models.TextField(default='', max_length=10000),
        ),
    ]
