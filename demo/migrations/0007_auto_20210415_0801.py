# Generated by Django 3.1.6 on 2021-04-15 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0006_auto_20210411_1225'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='logitem',
            constraint=models.UniqueConstraint(fields=('log_number', 'conversation'), name='Conversation contraint'),
        ),
    ]
