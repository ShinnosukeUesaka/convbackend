# Generated by Django 3.1.6 on 2021-09-21 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0019_auto_20210919_0828'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='options',
            field=models.TextField(default='{}', max_length=10000),
        ),
    ]