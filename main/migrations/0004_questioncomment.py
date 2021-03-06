# Generated by Django 3.2.5 on 2022-01-27 17:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_question_answer'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='main.question')),
            ],
        ),
    ]
