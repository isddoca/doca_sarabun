# Generated by Django 4.0.3 on 2022-03-13 02:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doc_record', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='docreceive',
            name='action',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='docsend',
            name='action',
            field=models.TextField(blank=True, null=True),
        ),
    ]
