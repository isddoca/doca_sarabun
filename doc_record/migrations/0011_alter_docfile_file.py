# Generated by Django 4.0.3 on 2022-03-22 03:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doc_record', '0010_remove_doc_filepath_alter_docreceive_send_to_docfile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='docfile',
            name='file',
            field=models.FileField(upload_to='doc/%Y%m%d'),
        ),
    ]
