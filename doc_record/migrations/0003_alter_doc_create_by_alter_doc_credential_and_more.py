# Generated by Django 4.0.3 on 2022-03-13 15:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('doc_record', '0002_docreceive_action_docsend_action'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doc',
            name='create_by',
            field=models.ForeignKey(blank=True, db_column='create_by', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='create_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='doc',
            name='credential',
            field=models.ForeignKey(blank=True, db_column='credential', null=True, on_delete=django.db.models.deletion.CASCADE, to='doc_record.doccredential'),
        ),
        migrations.AlterField(
            model_name='doc',
            name='update_by',
            field=models.ForeignKey(blank=True, db_column='update_by', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='update_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='doc',
            name='urgent',
            field=models.ForeignKey(blank=True, db_column='urgent', null=True, on_delete=django.db.models.deletion.CASCADE, to='doc_record.docurgent'),
        ),
        migrations.AlterField(
            model_name='docreceive',
            name='doc',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='doc_record.doc'),
        ),
        migrations.AlterField(
            model_name='docreceive',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='auth.group'),
        ),
        migrations.AlterField(
            model_name='docsend',
            name='doc',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='doc_record.doc'),
        ),
        migrations.AlterField(
            model_name='docsend',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='auth.group'),
        ),
        migrations.AlterField(
            model_name='doctrace',
            name='action_by',
            field=models.ForeignKey(blank=True, db_column='action_by', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='doctrace',
            name='doc_status',
            field=models.ForeignKey(db_column='doc_status', on_delete=django.db.models.deletion.CASCADE, to='doc_record.docstatus'),
        ),
    ]
