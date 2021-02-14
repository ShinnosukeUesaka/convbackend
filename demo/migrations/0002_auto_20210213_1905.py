# Generated by Django 3.1.6 on 2021-02-13 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='logitem',
            old_name='name_text',
            new_name='name',
        ),
        migrations.RemoveField(
            model_name='logitem',
            name='log',
        ),
        migrations.AddField(
            model_name='conversation',
            name='log_items',
            field=models.ManyToManyField(to='demo.LogItem'),
        ),
        migrations.DeleteModel(
            name='Log',
        ),
    ]