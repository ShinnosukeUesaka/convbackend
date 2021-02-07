# Generated by Django 3.1.6 on 2021-02-07 08:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Scenario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('initial_prompt', models.CharField(max_length=200)),
                ('ai_name', models.CharField(max_length=20)),
                ('human_name', models.CharField(max_length=20)),
                ('summarize_token', models.IntegerField()),
                ('info', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=100)),
                ('duration', models.IntegerField(choices=[(5, '5分'), (0, '10分'), (20, '20分')])),
                ('level', models.IntegerField(choices=[(1, '初心者'), (2, '中級者'), (3, '上級者')])),
            ],
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('conversation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='demo.conversation')),
            ],
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('scenario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='demo.scenario')),
            ],
        ),
        migrations.CreateModel(
            name='OptioinItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='demo.option')),
            ],
        ),
        migrations.AddField(
            model_name='conversation',
            name='scenario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='demo.scenario'),
        ),
        migrations.CreateModel(
            name='LogItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_text', models.CharField(max_length=20)),
                ('text', models.CharField(max_length=200)),
                ('is_hidden', models.BooleanField()),
                ('type', models.IntegerField(choices=[(1, 'Initial Prompt'), (2, 'Narration'), (3, 'Ai'), (4, 'Human')])),
                ('log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='demo.log')),
            ],
        ),
    ]
