# Generated by Django 3.1.6 on 2021-08-27 05:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0011_conversation_temp_for_conv_controller'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversation',
            name='temp_for_conv_controller',
            field=models.TextField(blank=True, default='{}', null=True),
        ),
        migrations.AlterField(
            model_name='logitem',
            name='name',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]