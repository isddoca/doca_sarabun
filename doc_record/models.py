import os
from datetime import datetime, timedelta

import pytz
from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from pythainlp import thai_strftime


class Doc(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    doc_no = models.CharField(max_length=64, blank=True, null=True)
    doc_date = models.DateField(blank=True, null=True)
    doc_from = models.CharField(max_length=200, blank=True, null=True)
    doc_to = models.CharField(max_length=200, blank=True, null=True)
    title = models.TextField()
    credential = models.ForeignKey('DocCredential', on_delete=models.CASCADE, db_column='credential', blank=True,
                                   null=True)
    urgent = models.ForeignKey('DocUrgent', on_delete=models.CASCADE, db_column='urgent', blank=True, null=True)
    active = models.IntegerField()
    create_time = models.DateTimeField(blank=True, null=True)
    create_by = models.ForeignKey(User, on_delete=models.CASCADE, db_column='create_by', blank=True, null=True,
                                  related_name='create_by')
    update_time = models.DateTimeField(blank=True, null=True)
    update_by = models.ForeignKey(User, on_delete=models.CASCADE, db_column='update_by', blank=True, null=True,
                                  related_name='update_by')

    def doc_date_th(self):
        return thai_strftime(datetime(self.doc_date.year, self.doc_date.month, self.doc_date.day), "%d %b %Y")

    class Meta:
        managed = True
        db_table = 'doc'


def update_doc_filename(instance, filename):
    path = "doc/{date}/{doc_id}".format(date=datetime.today().strftime('%Y%m%d'), doc_id=instance.doc.id)
    return os.path.join(path, filename)


class DocFile(models.Model):
    doc = models.ForeignKey(Doc, max_length=200, on_delete=models.CASCADE, blank=True, null=True)
    file = models.FileField(upload_to=update_doc_filename)

    class Meta:
        managed = True
        db_table = 'doc_file'

    def filename(self):
        return os.path.basename(self.file.name)


class DocCredential(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_credential'

    def __str__(self):
        return self.name


class DocSend(models.Model):
    send_no = models.IntegerField(blank=True, null=True)
    doc = models.ForeignKey(Doc, on_delete=models.CASCADE, blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True, related_name='send_group')
    send_to = models.ManyToManyField(Group, blank=True)
    action = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_send'


class DocStatus(models.Model):
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_status'


class DocTrace(models.Model):
    time = models.DateTimeField(blank=True, null=True)
    action_from = models.ForeignKey(Group, on_delete=models.CASCADE, db_column='action_from', blank=True, null=True,
                                    related_name='trace_action_from')
    action_to = models.ForeignKey(Group, on_delete=models.CASCADE, db_column='action_to', blank=True, null=True,
                                  related_name='trace_action_to')
    create_by = models.ForeignKey(User, on_delete=models.CASCADE, db_column='create_by', blank=True, null=True,
                                  related_name='trace_create_by')
    doc = models.ForeignKey(Doc, models.DO_NOTHING)
    done = models.BooleanField(default=False)
    doc_status = models.ForeignKey(DocStatus, on_delete=models.CASCADE, db_column='doc_status')
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_trace'

    def __str__(self):
        return self.action_to.name

    def time_th(self):
        return thai_strftime(self.time + timedelta(hours=7), "%d %b %Y, %H:%M")


class DocReceive(models.Model):
    receive_no = models.IntegerField(blank=True, null=True)
    doc = models.ForeignKey(Doc, on_delete=models.CASCADE, blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True, related_name='receive_group')
    send_to = models.ManyToManyField(Group, blank=True)
    action = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'doc_receive'


class DocUrgent(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

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
