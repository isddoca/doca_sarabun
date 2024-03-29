import os
from datetime import datetime

import environ
import pytz
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from config import settings
from doc_record.forms import DocReceiveModelForm, DocModelForm, DocCredentialModelForm
from doc_record.models import DocReceive, DocFile, DocTrace, Doc
from doc_record.views.base import generate_doc_id, get_line_id
from doc_record.views.linenotify import send_doc_notify

env = environ.Env()
environ.Env.read_env()


@method_decorator(login_required, name='dispatch')
class DocReceiveListView(ListView):
    model = DocReceive
    template_name = 'doc_record/receive_index.html'
    paginate_by = 20

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        year = self.request.GET.get('year', datetime.now().year)
        keyword = self.request.GET.get('keyword', '')

        return DocReceive.objects.filter(
            (Q(doc__title__contains=keyword) | Q(doc__doc_no__contains=keyword) |
             Q(doc__doc_from__contains=keyword) | Q(doc__doc_to__contains=keyword)) &
            Q(doc__create_time__year=year if year else datetime.now().year) & Q(group_id=current_group_id) & Q(
                doc__credential__id=1)) \
            .order_by('-receive_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DocReceiveListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct()
        context['title'] = "ทะเบียนหนังสือรับ"
        context['add_button'] = "ลงทะเบียนรับหนังสือ"
        context['add_path'] = "add"
        return context


@method_decorator(login_required, name='dispatch')
class DocReceiveCredentialListView(DocReceiveListView):
    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        year = self.request.GET.get('year', datetime.now().year)
        keyword = self.request.GET.get('keyword', '')

        return DocReceive.objects.filter(
            (Q(doc__title__contains=keyword) | Q(doc__doc_no__contains=keyword) |
             Q(doc__doc_from__contains=keyword) | Q(doc__doc_to__contains=keyword)) &
            Q(doc__create_time__year=year if year else datetime.now().year) & Q(group_id=current_group_id) & Q(
                doc__credential__id__gt=1)) \
            .order_by('-receive_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DocReceiveListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct()
        context['title'] = "ทะเบียนหนังสือรับ (ลับ)"
        context['add_button'] = "ลงทะเบียนรับหนังสือ (ลับ)"
        context['add_path'] = "credential/add"
        context['edit_path'] = "credential/"
        return context


@login_required(login_url='/accounts/login')
def doc_receive_detail(request, id):
    is_specific = 'credential' in request.path

    if is_specific:
        title = "รายละเอียดหนังสือ (ลับ)"
        parent_nav_title = "ทะเบียนหนังสือรับ (ลับ)"
        parent_nav_path = "/receive/credential"
    else:
        title = "รายละเอียดหนังสือ"
        parent_nav_title = "ทะเบียนหนังสือรับ "
        parent_nav_path = "/receive"

    doc_receive = DocReceive.objects.get(id=id)
    doc_old_files = DocFile.objects.filter(doc=doc_receive.doc)
    context = {'doc_receive': doc_receive, 'doc_files': doc_old_files, 'title': title,
               'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
    return render(request, 'doc_record/docreceive_view.html', context)


@login_required(login_url='/accounts/login')
def doc_receive_add(request):
    timezone = pytz.timezone('Asia/Bangkok')
    user = request.user
    current_group = user.groups.all()[0]
    parent_nav_title = "ทะเบียนหนังสือรับ"
    parent_nav_path = "/receive"
    title = "ลงทะเบียนรับหนังสือ"

    is_credential = 'credential' in request.path

    if request.method == 'POST':
        if 'credential' in request.path:
            doc_form = DocCredentialModelForm(request.POST, request.FILES, can_edit=True)
        else:
            doc_form = DocModelForm(request.POST, request.FILES, can_edit=True)
        doc_receive_form = DocReceiveModelForm(request.POST, groups_id=[current_group.id])

        if doc_form.is_valid() and doc_receive_form.is_valid():
            doc_model = doc_form.save(commit=False)
            doc_model.id = request.POST["doc_id"]
            doc_model.active = 1
            doc_model.create_time = datetime.now(timezone)
            doc_model.create_by = user
            doc_model.save()

            req_files = request.FILES.getlist('file')
            for f in req_files:
                DocFile.objects.create(file=f, doc=doc_model)

            doc_receive_model = doc_receive_form.save(commit=False)
            doc_receive_model.id = request.POST["receive_id"]
            doc_receive_model.doc = doc_model
            doc_receive_model.group = current_group
            doc_receive_model.save()
            doc_receive_form.save_m2m()

            send_to = doc_receive_model.send_to.all()
            DocTrace.objects.create(doc=doc_model, doc_status_id=1, create_by=user, action_from_id=current_group.id,
                                    done=True,
                                    action_to_id=current_group.id, time=datetime.now(timezone))

            get_line_id(send_to)

            for unit in send_to:
                doctrace = DocTrace.objects.create(doc=doc_model, doc_status_id=2, create_by=user, action_to=unit,
                                                   action_from_id=current_group.id, time=datetime.now(timezone))
                url = request.build_absolute_uri('/trace/pending/' + str(doctrace.pk))
                send_doc_notify(current_group, doc_model, unit, url)

            if is_credential:
                return HttpResponseRedirect('/receive/credential')
            else:
                return HttpResponseRedirect('/receive')
    else:
        send_no = get_receive_no(request.user, is_credential=is_credential)
        doc = Doc.objects.create(id=generate_doc_id(), credential_id=2 if is_credential else 1,
                                 active=True, create_by=user, create_time=datetime.now(timezone))
        doc.save()
        doc_receive = DocReceive.objects.create(receive_no=send_no, doc=doc, group=current_group)
        doc_receive.save()

        doc_receive_form = DocReceiveModelForm(instance=doc_receive, groups_id=[current_group.id])
        if is_credential:
            doc_form = DocCredentialModelForm(instance=doc, can_edit=True)
            title = "ลงทะเบียนรับหนังสือ (ลับ)"
            parent_nav_title = "ทะเบียนหนังสือรับ (ลับ)"
            parent_nav_path = "/receive/credential"
        else:
            doc_form = DocModelForm(instance=doc, can_edit=True)
            parent_nav_path = "/receive"

    context = {'doc_id': doc.id, 'receive_id': doc_receive.id, 'doc_form': doc_form,
               'doc_receive_form': doc_receive_form, 'title': title,
               'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
    return render(request, 'doc_record/docreceive_form.html', context)


@login_required(login_url='/accounts/login')
def doc_receive_edit(request, id):
    doc_receive = DocReceive.objects.get(id=id)
    timezone = pytz.timezone('Asia/Bangkok')
    current_group = request.user.groups.all()[0]
    parent_nav_title = "ทะเบียนหนังสือรับ"
    parent_nav_path = "/receive"
    title = "แก้ไขทะเบียนรับหนังสือ"

    is_secret = 'credential' in request.path
    can_edit_doc = current_group in doc_receive.doc.create_by.groups.all()

    doc_old_files = DocFile.objects.filter(doc=doc_receive.doc)
    if request.method == 'POST':
        user = request.user

        if is_secret:
            doc_form = DocCredentialModelForm(request.POST, request.FILES, can_edit=can_edit_doc)
        else:
            doc_form = DocModelForm(request.POST, request.FILES, can_edit=can_edit_doc)
        doc_receive_form = DocReceiveModelForm(request.POST, groups_id=[current_group.id])

        if doc_form.is_valid() and doc_receive_form.is_valid():
            if can_edit_doc:
                doc_model = doc_form.save(commit=False)
                doc_model.id = doc_receive.doc.id
                doc_model.active = 1
                doc_model.update_time = datetime.now(timezone)
                doc_model.update_by = user
                doc_model.create_time = doc_receive.doc.create_time
                doc_model.create_by = doc_receive.doc.create_by
                doc_model.save()
            else:
                doc_model = doc_receive.doc

            doc_receive_model = doc_receive_form.save(commit=False)
            doc_receive_model.id = doc_receive.id
            doc_receive_model.doc = doc_model
            doc_receive_model.group = current_group
            doc_receive_model.save()
            doc_receive_form.save_m2m()

            # ถ้าไม่มีไฟล์อัพเดท ไม่ต้องลบ ถ้ามีให้ลบแล้วเพิ่มใหม่
            files = request.FILES.getlist('file')
            if len(files) > 0:
                for f in doc_old_files:
                    os.remove(os.path.join(settings.MEDIA_ROOT, f.file.name))
                    f.delete()

                for f in files:
                    DocFile.objects.create(file=f, doc=doc_model)

            send_to = doc_receive_model.send_to.all()
            DocTrace.objects.get_or_create(doc=doc_model, doc_status_id=1, create_by=user,
                                           action_to=current_group, action_from=current_group, done=True,
                                           defaults={'time': datetime.now(timezone)})

            # หาหน่วยที่ทำเสร็จแล้ว
            done_traces = DocTrace.objects.filter(doc=doc_model, done=True)
            done_unit = []
            for trace in done_traces:
                done_unit.append(trace.action_to)

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
            if is_secret:
                return HttpResponseRedirect('/receive/credential')
            else:
                return HttpResponseRedirect('/receive')
    else:
        tmp_doc_date = doc_receive.doc.doc_date
        if tmp_doc_date:
            doc_receive.doc.doc_date = tmp_doc_date.replace(year=tmp_doc_date.year + 543)
        if 'credential' in request.path:
            doc_form = DocCredentialModelForm(instance=doc_receive.doc, can_edit=can_edit_doc)
            title = "แก้ไขทะเบียนรับหนังสือ (ลับ)"
            parent_nav_title = "ทะเบียนหนังสือรับ (ลับ)"
            parent_nav_path = "/receive/credential"
        else:
            doc_form = DocModelForm(instance=doc_receive.doc, can_edit=can_edit_doc)

            parent_nav_path = "/receive"
        doc_receive_form = DocReceiveModelForm(instance=doc_receive, groups_id=[current_group.id])
    print(doc_old_files)
    context = {'doc_form': doc_form, 'doc_receive_form': doc_receive_form, 'doc_files': doc_old_files, 'title': title,
               'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
    return render(request, 'doc_record/docreceive_form.html', context)


@login_required(login_url='/accounts/login')
def doc_receive_delete(request, id):
    if request.method == "POST":
        doc_receive = get_object_or_404(DocReceive, id=id)
        units = doc_receive.send_to.all()
        user = request.user
        # delete related trace
        my_doc_trace = DocTrace.objects.filter(
            (Q(create_by=user) | Q(action_to_id__in=user.groups.all())) & Q(doc=doc_receive.doc))
        my_doc_trace.delete()
        # delete send to trace
        for unit in units:
            doc_trace = DocTrace.objects.filter(action_to=unit, doc=doc_receive.doc)
            doc_trace.delete()
        doc_receive.delete()
        doc = doc_receive.doc
        if doc.create_by == user:
            doc.delete()
    if 'credential' in request.path:
        return HttpResponseRedirect('/receive/credential')
    else:
        return HttpResponseRedirect('/receive')


def get_receive_no(user, is_credential=False):
    current_group_id = user.groups.all()[0].id
    if is_credential:
        docs = DocReceive.objects.filter(group_id=current_group_id, doc__credential__id__gt=1,
                                         doc__create_time__year=datetime.now().year).order_by('receive_no')
    else:
        docs = DocReceive.objects.filter(group_id=current_group_id, doc__credential__id=1,
                                         doc__create_time__year=datetime.now().year).order_by('receive_no')
    return 1 if len(docs) == 0 else docs.last().receive_no + 1
