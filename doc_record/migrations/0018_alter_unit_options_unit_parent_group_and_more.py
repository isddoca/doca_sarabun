# Generated by Django 4.1.6 on 2023-03-07 07:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('doc_record', '0017_linenotifytoken'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='unit',
            options={'managed': True},
        ),
        migrations.AddField(
            model_name='unit',
            name='parent_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent_unit', to='auth.group'),
        ),
        migrations.AlterModelTable(
            name='unit',
            table='groups_unit',
        ),
    ]