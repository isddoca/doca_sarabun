from django.contrib import auth
from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Doc(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    doc_no = models.CharField(max_length=64, blank=True, null=True)
    doc_date = models.DateField(blank=True, null=True)
    doc_from = models.CharField(max_length=200, blank=True, null=True)
    doc_to = models.CharField(max_length=200, blank=True, null=True)
    title = models.TextField()
    credential = models.ForeignKey('DocCredential', models.DO_NOTHING, db_column='credential', blank=True, null=True)
    urgent = models.ForeignKey('DocUrgent', models.DO_NOTHING, db_column='urgent', blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    active = models.IntegerField()
    create_time = models.DateTimeField(blank=True, null=True)
    create_by = models.ForeignKey(User, models.DO_NOTHING, db_column='create_by', blank=True, null=True, related_name='create_by')
    update_time = models.DateTimeField(blank=True, null=True)
    update_by = models.ForeignKey(User, models.DO_NOTHING, db_column='update_by', blank=True, null=True, related_name='update_by')
    filepath = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc'


class DocCredential(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_credential'


class DocReceive(models.Model):
    doc = models.ForeignKey(Doc, models.DO_NOTHING)
    receive_no = models.IntegerField(blank=True, null=True)
    group = models.ForeignKey(Group, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_receive'

class DocSend(models.Model):
    id = models.IntegerField(primary_key=True)
    doc = models.ForeignKey(Doc, models.DO_NOTHING, blank=True, null=True)
    send_no = models.IntegerField(blank=True, null=True)
    group = models.ForeignKey(Group, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_send'


class DocStatus(models.Model):
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_status'


class DocTrace(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    doc = models.ForeignKey(Doc, models.DO_NOTHING)
    doc_status = models.ForeignKey(DocStatus, models.DO_NOTHING, db_column='doc_status')
    time = models.DateTimeField(blank=True, null=True)
    action_by = models.ForeignKey(User, models.DO_NOTHING, db_column='action_by', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_trace'


class DocUrgent(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_urgent'


class Unit(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    unit_id = models.CharField(max_length=64, blank=True, null=True)


@receiver(post_save, sender=Group)
def create_group_unit(sender, instance, created, **kwargs):
    if created:
        Unit.objects.create(group=instance)
    instance.unit.save()


