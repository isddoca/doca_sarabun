# Generated by Django 4.0.3 on 2022-03-24 05:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('doc_record', '0012_doctrace_success_alter_docfile_file'),
    ]

    operations = [
        migrations.RenameField(
            model_name='doctrace',
            old_name='success',
            new_name='done',
        ),
    ]
