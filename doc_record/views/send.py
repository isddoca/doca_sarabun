import os
from datetime import datetime, date

import pytz
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from config import settings
from doc_record.forms import DocModelForm, DocCredentialModelForm, DocSendModelForm
from doc_record.models import DocFile, DocTrace, Doc, DocSend
from doc_record.views.base import generate_doc_id
from doc_record.views.linenotify import send_doc_notify


@method_decorator(login_required, name='dispatch')
class DocSendListView(ListView):
    model = DocSend
    template_name = 'doc_record/send_index.html'
    paginate_by = 20

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        year = self.request.GET.get('year', datetime.now().year)
        keyword = self.request.GET.get('keyword', '')

        return DocSend.objects.filter(
            (Q(doc__title__contains=keyword) | Q(doc__doc_no__contains=keyword) |
             Q(doc__doc_from__contains=keyword) | Q(doc__doc_to__contains=keyword)) &
            Q(doc__create_time__year=year if year else datetime.now().year) & Q(group_id=current_group_id) & Q(
                doc__credential__id=1)) \
            .order_by('-send_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        parent_group = Group.objects.get(id=self.kwargs.get('group_id'))
        context = super(DocSendListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct()
        context['current_group'] = self.request.user.groups.all()[0]
        context['title'] = "ทะเบียนหนังสือส่งออก{}".format(parent_group.unit.unit_level)
        context['add_button'] = "ลงทะเบียนหนังสือส่งออก{}".format(parent_group.unit.unit_level)
        context['add_path'] = str(parent_group.id) + "/add"
        context['edit_path'] = str(parent_group.id) + "/"
        return context


@method_decorator(login_required, name='dispatch')
class DocSendCredentialListView(DocSendListView):
    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        year = self.request.GET.get('year', datetime.now().year)
        keyword = self.request.GET.get('keyword', '')

        return DocSend.objects.filter(
            (Q(doc__title__contains=keyword) | Q(doc__doc_no__contains=keyword) |
             Q(doc__doc_from__contains=keyword) | Q(doc__doc_to__contains=keyword)) &
            Q(doc__create_time__year=year if year else datetime.now().year) & Q(group_id=current_group_id) & Q(
                doc__credential__id__gt=1)) \
            .order_by('-send_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DocSendListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct()
        context['current_group'] = self.request.user.groups.all()[0]
        context['title'] = "ทะเบียนหนังสือส่ง (ลับ)"
        context['add_button'] = "ลงทะเบียนส่งหนังสือ (ลับ)"
        context['add_path'] = "credential/add"
        context['edit_path'] = "credential/"
        return context


@login_required(login_url='/accounts/login')
def doc_send_detail(request, group_id, id):
    title = "รายละเอียดหนังสือ"
    parent_group = Group.objects.get(id=group_id)
    current_user_group = request.user.groups.all()[0]
    is_sent_outside = parent_group != current_user_group
    is_credential = 'credential' in request.path

    if is_credential:
        if is_sent_outside:
            parent_nav_title = "ทะเบียนหนังสือส่งออก{} (ลับ)".format(parent_group.unit.unit_level)
            parent_nav_path = "/send/out/credential"
        else:
            parent_nav_title = "ทะเบียนหนังสือส่ง (ลับ)"
            parent_nav_path = "/send/credential"
    else:
        if is_sent_outside:
            parent_nav_title = "ทะเบียนหนังสือส่งออก{}".format(parent_group.unit.unit_level)
            parent_nav_path = "/send/out"
        else:
            parent_nav_title = "ทะเบียนหนังสือส่ง"
            parent_nav_path = "/send"

    doc_send = DocSend.objects.get(id=id)
    doc_old_files = DocFile.objects.filter(doc=doc_send.doc)
    context = {'doc_send': doc_send, 'doc_files': doc_old_files, 'title': title,
               'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
    return render(request, 'doc_record/docsend_view.html', context)


@login_required(login_url='/accounts/login')
def doc_send_add(request, group_id):
    timezone = pytz.timezone('Asia/Bangkok')
    user = request.user

    parent_group = Group.objects.get(id=group_id)
    current_user_group = request.user.groups.all()[0]

    current_group = user.groups.all()[0]
    doca_group = Group.objects.get(id=1)

    is_sent_outside = "out" in request.path
    is_credential = 'credential' in request.path

    if is_credential:
        if is_sent_outside:
            parent_nav_title = "ทะเบียนหนังสือส่งออก{} (ลับ)".format(parent_group.unit.unit_level)
            parent_nav_path = "/send/out/credential"
        else:
            parent_nav_title = "ทะเบียนหนังสือส่ง (ลับ)"
            parent_nav_path = "/send/credential"
    else:
        if is_sent_outside:
            parent_nav_title = "ทะเบียนหนังสือส่งออก{}".format(parent_group.unit.unit_level)
            parent_nav_path = "/send/out"
        else:
            parent_nav_title = "ทะเบียนหนังสือส่ง"
            parent_nav_path = "/send"

    title = "ลงทะเบียนส่งหนังสือ"

    unit_group = doca_group if is_sent_outside else current_group

    if request.method == 'POST':
        if is_credential:
            doc_form = DocCredentialModelForm(request.POST, request.FILES, can_edit=True)
        else:
            doc_form = DocModelForm(request.POST, request.FILES, can_edit=True)
        doc_send_form = DocSendModelForm(request.POST, groups_id=[current_group.id])

        if doc_form.is_valid() and doc_send_form.is_valid():
            doc_model = doc_form.save(commit=False)
            doc_model.id = request.POST["doc_id"]
            doc_model.active = 1
            doc_model.create_time = datetime.now(timezone)
            doc_model.create_by = user
            doc_model.save()

            req_files = request.FILES.getlist('file')
            for f in req_files:
                DocFile.objects.create(file=f, doc=doc_model)

            doc_send_model = doc_send_form.save(commit=False)
            doc_send_model.id = request.POST["send_id"]
            doc_send_model.doc = doc_model
            doc_send_model.group = unit_group
            doc_send_model.save()
            doc_send_form.save_m2m()

            send_to = doc_send_model.send_to.all()
            for unit in send_to:
                doc_trace = DocTrace.objects.create(doc=doc_model, doc_status_id=2, create_by=user, action_to=unit,
                                                    action_from=current_group, time=datetime.now(timezone))
                url = request.build_absolute_uri('/trace/pending/' + str(doc_trace.pk))
                send_doc_notify(current_group, doc_model, unit, url)
            return HttpResponseRedirect(return_page(request, group_id))
    else:
        send_no = get_send_no(request.user, is_secret=is_credential, is_outside=is_sent_outside)
        doc_no = get_doc_no(current_group, is_outside=is_sent_outside, send_no=send_no)

        doc = Doc.objects.create(id=generate_doc_id(), doc_no=doc_no, credential_id=2 if is_credential else 1,
                                 active=True, create_by=user, create_time=datetime.now(timezone))
        doc.save()
        doc_id = doc.id
        doc_send = DocSend.objects.create(send_no=send_no, doc=doc, group=unit_group)
        doc_send.save()
        send_id = doc_send.id

        doc_send_form = DocSendModelForm(instance=doc_send, groups_id=[unit_group.id])
        if is_credential:
            doc_form = DocCredentialModelForm(instance=doc, can_edit=True)
            if is_sent_outside:
                parent_nav_title = "ทะเบียนหนังสือส่งภายนอกหน่วย (ลับ)"
                parent_nav_path = "/send/out/credential"
                title = "ลงทะเบียนส่งหนังสือภายนอกหน่วย (ลับ)"
            else:
                parent_nav_title = "ทะเบียนหนังสือส่ง (ลับ)"
                parent_nav_path = "/send/credential"
                title = "ลงทะเบียนส่งหนังสือ (ลับ)"
        else:
            doc_form = DocModelForm(instance=doc, can_edit=True)
            if is_sent_outside:
                parent_nav_title = "ทะเบียนหนังสือส่งภายนอกหน่วย"
                parent_nav_path = "/send/out"
                title = "ลงทะเบียนส่งหนังสือภายนอกหน่วย"

        context = {'doc_id': doc_id, 'send_id': send_id, 'doc_form': doc_form, 'doc_send_form': doc_send_form,
                   'title': title, 'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
        return render(request,
                      'doc_record/docsend_out_form.html' if is_sent_outside else 'doc_record/docsend_form.html',
                      context)


@login_required(login_url='/accounts/login')
def doc_send_edit(request, id):
    doc_send = DocSend.objects.get(id=id)
    timezone = pytz.timezone('Asia/Bangkok')
    current_group = request.user.groups.all()[0]

    parent_nav_title = "ทะเบียนหนังสือส่ง"
    parent_nav_path = "/send"
    title = "แก้ไขทะเบียนส่งหนังสือ"

    is_sent_outside = "out" in request.path
    is_credential = 'credential' in request.path
    can_edit_doc = current_group in doc_send.doc.create_by.groups.all()

    doc_old_files = DocFile.objects.filter(doc=doc_send.doc)
    if request.method == 'POST':
        user = request.user

        if is_credential:
            doc_form = DocCredentialModelForm(request.POST, request.FILES, can_edit=can_edit_doc)
        else:
            doc_form = DocModelForm(request.POST, request.FILES, can_edit=can_edit_doc)
        doc_send_form = DocSendModelForm(request.POST, groups_id=[current_group.id])

        if doc_form.is_valid() and doc_send_form.is_valid():
            if can_edit_doc:
                doc_model = doc_form.save(commit=False)
                doc_model.id = doc_send.doc.id
                doc_model.active = 1
                doc_model.update_time = datetime.now(timezone)
                doc_model.update_by = user
                doc_model.create_time = doc_send.doc.create_time
                doc_model.create_by = doc_send.doc.create_by
                doc_model.save()
            else:
                doc_model = doc_send.doc

            doc_send_model = doc_send_form.save(commit=False)
            doc_send_model.id = doc_send.id
            doc_send_model.doc = doc_model
            doc_send_model.group = Group.objects.get(id=1) if is_sent_outside else current_group
            doc_send_model.save()
            doc_send_form.save_m2m()

            # ถ้าไม่มีไฟล์อัพเดท ไม่ต้องลบ ถ้ามีให้ลบแล้วเพิ่มใหม่
            files = request.FILES.getlist('file')
            if len(files) > 0:
                for f in doc_old_files:
                    os.remove(os.path.join(settings.MEDIA_ROOT, f.file.name))
                    f.delete()

                for f in files:
                    DocFile.objects.create(file=f, doc=doc_model)

            send_to = doc_send_model.send_to.all()

            # หาหน่วยที่ทำเสร็จแล้ว
            doc_traces = DocTrace.objects.filter(doc=doc_model)
            done_unit = []
            for trace in doc_traces:
                if trace.done:
                    done_unit.append(trace.action_to)

                if trace.action_to not in send_to:
                    unused_trace = DocTrace.objects.filter(doc=doc_model, action_to=trace.action_to)
                    unused_trace.delete()

            for unit in send_to:
                if unit not in done_unit:  # เพิ่มหรือแก้ไขประวัติการส่งเฉพาะหน่วยที่ยังดำเนินการไม่เสร็จ
                    doc_trace, is_create = DocTrace.objects.update_or_create(doc=doc_model, doc_status_id=2,
                                                                             action_from=current_group,
                                                                             action_to=unit,
                                                                             defaults={'time': datetime.now(timezone),
                                                                                       'create_by': user})
                    if is_create:  # เตือนเฉพาะหน่วยที่เพิ่มใหม่เท่านั้น
                        url = request.build_absolute_uri('/trace/pending/' + str(doc_trace.pk))
                        send_doc_notify(current_group, doc_model, unit, url)
            return return_page(request)
    else:
        tmp_doc_date = doc_send.doc.doc_date
        if tmp_doc_date:
            doc_send.doc.doc_date = tmp_doc_date.replace(year=tmp_doc_date.year + 543)
        doc_send_form = DocSendModelForm(instance=doc_send, groups_id=[current_group.id])
        if is_credential:
            if is_sent_outside:
                parent_nav_title = "ทะเบียนหนังสือส่งภายนอกหน่วย (ลับ)"
                parent_nav_path = "/send/out/credential"
                title = "แก้ไขทะเบียนส่งหนังสือภายนอกหน่วย (ลับ)"
            else:
                parent_nav_title = "ทะเบียนหนังสือส่ง (ลับ)"
                parent_nav_path = "/send/credential"
                title = "แก้ไขทะเบียนส่งหนังสือ (ลับ)"
            doc_form = DocCredentialModelForm(instance=doc_send.doc, can_edit=can_edit_doc)
        else:
            if is_sent_outside:
                parent_nav_title = "ทะเบียนหนังสือส่งภายนอกหน่วย"
                parent_nav_path = "/send/out"
                title = "แก้ไขทะเบียนส่งหนังสือภายนอกหน่วย"
            doc_form = DocModelForm(instance=doc_send.doc, can_edit=can_edit_doc)

    context = {'doc_form': doc_form, 'doc_send_form': doc_send_form, 'doc_files': doc_old_files, 'title': title,
               'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
    return render(request, 'doc_record/docsend_out_form.html' if is_sent_outside else 'doc_record/docsend_form.html',
                  context)


@login_required(login_url='/accounts/login')
def doc_send_delete(request, group_id, id):
    if request.method == "POST":
        doc_send = get_object_or_404(DocSend, id=id)
        units = doc_send.send_to.all()
        user = request.user
        for unit in units:
            doc_trace = DocTrace.objects.filter(action_to=unit, doc=doc_send.doc)
            doc_trace.delete()
        doc_send.delete()
        doc = doc_send.doc
        if doc.create_by == user:
            doc.delete()
    return HttpResponseRedirect(return_page(request, group_id))


def return_page(request, group_id):
    if 'credential' in request.path:
        return_path = '/send/unit/{}/credential'.format(group_id)
    else:
        return_path = '/send/unit/{}'.format(group_id)
    return return_path


def get_send_no(user, is_secret=False, is_outside=False):
    # DOCA is id 1
    current_group_id = 1 if is_outside else user.groups.all()[0].id

    if is_secret:
        docs = DocSend.objects.filter(group_id=current_group_id, doc__credential__id__gt=1,
                                      doc__create_time__year=datetime.now().year).order_by('send_no')
    else:
        docs = DocSend.objects.filter(group_id=current_group_id, doc__credential__id=1,
                                      doc__create_time__year=datetime.now().year).order_by('send_no')
    return 1 if len(docs) == 0 else docs.last().send_no + 1


def get_doc_no(group, is_outside=False, send_no=-1):
    group = Group.objects.get(id=1) if is_outside else group  # doca_group
    return 'กห ' + group.unit.unit_id + '/' + str(send_no)
