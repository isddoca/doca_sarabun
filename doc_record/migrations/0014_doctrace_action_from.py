# Generated by Django 4.0.3 on 2022-03-25 08:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('doc_record', '0013_rename_success_doctrace_done'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctrace',
            name='action_from',
            field=models.ForeignKey(blank=True, db_column='action_from', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='trace_action_from', to='auth.group'),
        ),
    ]
