# Generated by Django 3.1.6 on 2021-09-19 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0016_auto_20210916_0754'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scenario',
            name='info',
        ),
        migrations.AddField(
            model_name='scenario',
            name='article',
            field=models.TextField(blank=True, default='', max_length=10000, null=True),
        ),
    ]
