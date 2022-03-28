import os
from datetime import datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from config import settings
from doc_record.forms import DocModelForm, DocCredentialModelForm, DocSendModelForm
from doc_record.models import DocFile, DocTrace, Doc, DocSend
from doc_record.views.base import generate_doc_id


@method_decorator(login_required, name='dispatch')
class DocSendListView(ListView):
    model = DocSend
    template_name = 'doc_record/send_index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        search = self.request.GET.get('year', datetime.now().year)
        return DocSend.objects.filter(group_id=current_group_id, doc__create_time__year=search,
                                      doc__credential__id=1).order_by('-send_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DocSendListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct()
        context['title'] = "ทะเบียนหนังสือส่ง"
        context['add_button'] = "ลงทะเบียนส่งหนังสือ"
        context['add_path'] = "add"
        return context


@method_decorator(login_required, name='dispatch')
class DocSendCredentialListView(DocSendListView):
    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        search = self.request.GET.get('year', datetime.now().year)
        return DocSend.objects.filter(group_id=current_group_id, doc__create_time__year=search,
                                      doc__credential__id__gt=1).order_by('-send_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DocSendListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct()
        context['title'] = "ทะเบียนหนังสือส่ง (ลับ)"
        context['add_button'] = "ลงทะเบียนส่งหนังสือ (ลับ)"
        context['add_path'] = "credential/add"
        context['edit_path'] = "credential/"
        return context


@method_decorator(login_required, name='dispatch')
class DocSendOutListView(DocSendListView):
    def get_queryset(self):
        doca_group = Group.objects.get(id=1)
        current_group_id = self.request.user.groups.all()[0].id
        search = self.request.GET.get('year', datetime.now().year)
        return DocSend.objects.filter(group_id=doca_group, doc__create_time__year=search,
                                      doc__create_by__groups=current_group_id,
                                      doc__credential__id=1).order_by('-send_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DocSendListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct()
        context['title'] = "ทะเบียนหนังสือนอกหน่วย"
        context['add_button'] = "ลงทะเบียนส่งหนังสือนอกหน่วย"
        context['add_path'] = "out/add"
        context['edit_path'] = "out/"
        return context


@method_decorator(login_required, name='dispatch')
class DocSendCredentialOutListView(DocSendListView):
    def get_queryset(self):
        doca_group = Group.objects.get(id=1)
        current_group_id = self.request.user.groups.all()[0].id
        search = self.request.GET.get('year', datetime.now().year)
        return DocSend.objects.filter(group_id=doca_group, doc__create_time__year=search,
                                      doc__create_by__groups=current_group_id,
                                      doc__credential__id__gt=1).order_by('-send_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DocSendListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct()
        context['title'] = "ทะเบียนหนังสือนอกหน่วย (ลับ)"
        context['add_button'] = "ลงทะเบียนส่งหนังสือนอกหน่วย (ลับ)"
        context['add_path'] = "credential/add"
        context['edit_path'] = "credential/"
        return context


@login_required(login_url='/accounts/login')
def doc_send_detail(request, id):
    doc_send = DocSend.objects.get(id=id)
    doc_old_files = DocFile.objects.filter(doc=doc_send.doc)
    context = {'doc_send': doc_send, 'doc_files': doc_old_files}
    return render(request, 'doc_record/docsend_view.html', context)


@login_required(login_url='/accounts/login')
def doc_send_add(request):
    timezone = pytz.timezone('Asia/Bangkok')
    user = request.user
    group = user.groups.all()[0]

    parent_nav_title = "ทะเบียนหนังสือส่ง"
    parent_nav_path = "/send"
    title = "ลงทะเบียนส่งหนังสือ"

    is_sent_outside = "out" in request.path
    is_credential = 'credential' in request.path
    if request.method == 'POST':
        if is_credential:
            doc_form = DocCredentialModelForm(request.POST, request.FILES)
        else:
            doc_form = DocModelForm(request.POST, request.FILES)
        doc_send_form = DocSendModelForm(request.POST)

        if doc_form.is_valid() and doc_send_form.is_valid():
            doc_model = doc_form.save(commit=False)
            doc_model.id = generate_doc_id()
            doc_model.active = 1
            doc_model.create_time = datetime.now(timezone)
            doc_model.create_by = user
            doc_model.save()

            req_files = request.FILES.getlist('file')
            for f in req_files:
                DocFile.objects.create(file=f, doc=doc_model)

            doc_send_model = doc_send_form.save(commit=False)
            doc_send_model.doc = doc_model
            doc_send_model.group = Group.objects.get(id=1) if is_sent_outside else user.groups.all()[0]
            doc_send_model.save()
            doc_send_form.save_m2m()

            if is_sent_outside:
                if is_credential:
                    return HttpResponseRedirect('/send/out/credential')
                else:
                    return HttpResponseRedirect('/send/out')
            else:
                send_to = doc_send_model.send_to.all()
                for unit in send_to:
                    DocTrace.objects.create(doc=doc_model, doc_status_id=2, create_by=user, action_to=unit,
                                            action_from=group, time=datetime.now(timezone))
                if is_credential:
                    return HttpResponseRedirect('/send/credential')
                else:
                    return HttpResponseRedirect('/send')

    else:
        send_no = get_send_no(request.user, is_secret=is_credential, is_outside=is_sent_outside)
        doc_no = get_doc_no(group, is_outside=is_sent_outside, send_no=send_no)
        doc_send_form = DocSendModelForm(initial={'send_no': send_no})
        if is_credential:
            doc_form = DocCredentialModelForm(initial={'id': generate_doc_id(), 'doc_no': doc_no})
            if is_sent_outside:
                parent_nav_title = "ทะเบียนหนังสือส่งภายนอกหน่วย (ลับ)"
                parent_nav_path = "/send/credential/out"
                title = "ลงทะเบียนส่งหนังสือภายนอกหน่วย (ลับ)"
            else:
                parent_nav_title = "ทะเบียนหนังสือส่ง (ลับ)"
                parent_nav_path = "/send/credential"
                title = "ลงทะเบียนส่งหนังสือ (ลับ)"
        else:
            doc_form = DocModelForm(initial={'id': generate_doc_id(), 'doc_no': doc_no})
            if is_sent_outside:
                parent_nav_title = "ทะเบียนหนังสือส่งภายนอกหน่วย"
                parent_nav_path = "/send/credential/out"
                title = "ลงทะเบียนส่งหนังสือภายนอกหน่วย"

    context = {'doc_form': doc_form, 'doc_send_form': doc_send_form, 'title': title,
               'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
    return render(request, 'doc_record/docsend_out_form.html' if is_sent_outside else 'doc_record/docsend_form.html',
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

    doc_old_files = DocFile.objects.filter(doc=doc_send.doc)
    if request.method == 'POST':
        user = request.user

        if is_credential:
            doc_form = DocCredentialModelForm(request.POST, request.FILES)
        else:
            doc_form = DocModelForm(request.POST, request.FILES)
        doc_send_form = DocSendModelForm(request.POST)

        if doc_form.is_valid() and doc_send_form.is_valid():
            doc_model = doc_form.save(commit=False)
            doc_model.id = doc_send.doc.id
            doc_model.active = 1
            doc_model.update_time = datetime.now(timezone)
            doc_model.update_by = user
            doc_model.create_time = doc_send.doc.create_time
            doc_model.create_by = doc_send.doc.create_by
            doc_model.save()

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
            for unit in send_to:
                DocTrace.objects.update_or_create(doc=doc_model, doc_status_id=2, create_by=user,
                                                  action_from=current_group, action_to=unit,
                                                  defaults={'time': datetime.now(timezone)})

            if is_sent_outside:
                if is_credential:
                    return HttpResponseRedirect('/send/out/credential')
                else:
                    return HttpResponseRedirect('/send/out')
            else:
                if is_credential:
                    return HttpResponseRedirect('/send/credential')
                else:
                    return HttpResponseRedirect('/send')
    else:
        tmp_doc_date = doc_send.doc.doc_date
        doc_send.doc.doc_date = tmp_doc_date.replace(year=2565)
        if is_credential:
            if is_sent_outside:
                parent_nav_title = "ทะเบียนหนังสือส่งภายนอกหน่วย (ลับ)"
                parent_nav_path = "/send/credential/out"
                title = "แก้ไขทะเบียนส่งหนังสือภายนอกหน่วย (ลับ)"
            else:
                parent_nav_title = "ทะเบียนหนังสือส่ง (ลับ)"
                parent_nav_path = "/send/credential"
                title = "แก้ไขทะเบียนส่งหนังสือ (ลับ)"
            doc_form = DocCredentialModelForm(instance=doc_send.doc)
            doc_send_form = DocSendModelForm(instance=doc_send)
        else:
            if is_sent_outside:
                parent_nav_title = "ทะเบียนหนังสือส่งภายนอกหน่วย"
                parent_nav_path = "/send/out"
                title = "แก้ไขทะเบียนส่งหนังสือภายนอกหน่วย"
            doc_form = DocModelForm(instance=doc_send.doc)
            doc_send_form = DocSendModelForm(instance=doc_send)

    context = {'doc_form': doc_form, 'doc_send_form': doc_send_form, 'doc_files': doc_old_files, 'title': title,
               'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
    return render(request, 'doc_record/docsend_out_form.html' if is_sent_outside else 'doc_record/docsend_form.html',
                  context)


@login_required(login_url='/accounts/login')
def doc_send_delete(request, id):
    if request.method == "POST":
        doc_send = get_object_or_404(DocSend, id=id)
        units = doc_send.send_to.all()
        for unit in units:
            doc_trace = DocTrace.objects.filter(action_to=unit, doc=doc_send.doc)
            doc_trace.delete()
        doc_send.delete()
    if 'credential' in request.path:
        return HttpResponseRedirect('/send/credential')
    else:
        return HttpResponseRedirect('/send')


def get_send_no(user, is_secret=False, is_outside=False):
    # DOCA is id 1
    current_group_id = 1 if is_outside else user.groups.all()[0].id

    if is_secret:
        docs = DocSend.objects.filter(group_id=current_group_id, doc__credential__id__gt=1,
                                      doc__create_time__year=datetime.now().year)
    else:
        docs = DocSend.objects.filter(group_id=current_group_id, doc__credential__id=1,
                                      doc__create_time__year=datetime.now().year)
        print(datetime.now().year)
    return 1 if len(docs) == 0 else docs.last().send_no + 1


def get_doc_no(group, is_outside=False, send_no=-1):
    group = Group.objects.get(id=1) if is_outside else group  # doca_group
    return 'กห ' + group.unit.unit_id + '/' + str(send_no)
