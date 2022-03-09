# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import User

class DocCredential(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'doc_credential'


class DocUrgent(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'doc_urgent'


class ReceiveDoc(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    receive_no = models.IntegerField()
    doc_no = models.CharField(max_length=64, blank=True, null=True)
    doc_date = models.DateField(blank=True, null=True)
    doc_from = models.CharField(max_length=200, blank=True, null=True)
    doc_to = models.CharField(max_length=200, blank=True, null=True)
    title = models.TextField()
    credential = models.ForeignKey(DocCredential, models.DO_NOTHING, db_column='credential')
    urgent = models.ForeignKey(DocUrgent, models.DO_NOTHING, db_column='urgent', blank=True, null=True)
    action = models.TextField()
    note = models.IntegerField(blank=True, null=True)
    create_time = models.IntegerField(blank=True, null=True)
    create_by = models.ForeignKey(User, models.DO_NOTHING, db_column='create_by', blank=True, null=True)
    update_time = models.IntegerField(blank=True, null=True)
    update_by = models.ForeignKey(User, models.DO_NOTHING, db_column='update_by', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'receive_doc'


class SendDoc(models.Model):
    id = models.CharField(max_length=64, blank=True, null=True)
    send_no = models.IntegerField(blank=True, null=True)
    doc_no = models.CharField(max_length=64, blank=True, null=True)
    doc_date = models.DateField(blank=True, null=True)
    doc_from = models.CharField(max_length=200, blank=True, null=True)
    doc_to = models.CharField(max_length=200, blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    credential = models.ForeignKey(DocCredential, models.DO_NOTHING, db_column='credential', blank=True, null=True)
    urgent = models.ForeignKey(DocUrgent, models.DO_NOTHING, db_column='urgent', blank=True, null=True)
    action = models.TextField(blank=True, null=True)
    note = models.IntegerField(blank=True, null=True)
    create_time = models.IntegerField(blank=True, null=True)
    create_by = models.ForeignKey(User, models.DO_NOTHING, db_column='create_by', blank=True, null=True)
    update_time = models.IntegerField(blank=True, null=True)
    update_by = models.ForeignKey(User, models.DO_NOTHING, db_column='update_by', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'send_doc'
