import os
from datetime import datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from config import settings
from doc_record.forms import DocReceiveModelForm, DocModelForm, DocCredentialModelForm
from doc_record.models import DocReceive, DocFile, DocTrace, Doc
from doc_record.views.base import generate_doc_id


@method_decorator(login_required, name='dispatch')
class DocReceiveListView(ListView):
    model = DocReceive
    template_name = 'doc_record/receive_index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        search = self.request.GET.get('year', datetime.now().year)
        return DocReceive.objects.filter(group_id=current_group_id, doc__create_time__year=search,
                                         doc__credential__id=1).order_by('-receive_no')

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
        search = self.request.GET.get('year', datetime.now().year)
        return DocReceive.objects.filter(group_id=current_group_id, doc__create_time__year=search,
                                         doc__credential__id__gt=1).order_by('-receive_no')

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
    doc_receive = DocReceive.objects.get(id=id)
    doc_old_files = DocFile.objects.filter(doc=doc_receive.doc)
    context = {'doc_receive': doc_receive, 'doc_files': doc_old_files}
    return render(request, 'doc_record/docreceive_view.html', context)


@login_required(login_url='/accounts/login')
def doc_receive_add(request):
    timezone = pytz.timezone('Asia/Bangkok')
    user = request.user
    group_id = user.groups.all()[0].id
    parent_nav_title = "ทะเบียนหนังสือรับ"
    parent_nav_path = "/receive"
    title = "ลงทะเบียนรับหนังสือ"
    if request.method == 'POST':
        if 'credential' in request.path:
            doc_form = DocCredentialModelForm(request.POST, request.FILES)
        else:
            doc_form = DocModelForm(request.POST, request.FILES)

        doc_receive_form = DocReceiveModelForm(request.POST)

        if doc_form.is_valid() and doc_receive_form.is_valid():
            doc_model = doc_form.save(commit=False)
            doc_model.id = generate_doc_id()
            doc_model.active = 1
            doc_model.create_time = datetime.now(timezone)
            doc_model.create_by = user
            doc_model.save()

            req_files = request.FILES.getlist('file')
            for f in req_files:
                DocFile.objects.create(file=f, doc=doc_model)

            doc_receive_model = doc_receive_form.save(commit=False)
            doc_receive_model.doc = doc_model
            doc_receive_model.group = user.groups.all()[0]
            doc_receive_model.save()
            doc_receive_form.save_m2m()

            send_to = doc_receive_model.send_to.all()
            DocTrace.objects.create(doc=doc_model, doc_status_id=1, create_by=user, action_from_id=group_id, done=True,
                                    action_to_id=group_id, time=datetime.now(timezone))
            for unit in send_to:
                DocTrace.objects.create(doc=doc_model, doc_status_id=2, create_by=user, action_to=unit,
                                        action_from_id=group_id, time=datetime.now(timezone))

            if 'credential' in request.path:
                return HttpResponseRedirect('/receive/credential')
            else:
                return HttpResponseRedirect('/receive')
    else:
        if 'credential' in request.path:
            doc_form = DocCredentialModelForm(initial={'id': generate_doc_id()})
            doc_receive_form = DocReceiveModelForm(initial={'receive_no': get_docs_no(request.user, is_secret=True)})
            title = "ลงทะเบียนรับหนังสือ (ลับ)"
            parent_nav_path = "/receive/credential"
        else:
            doc_form = DocModelForm(initial={'id': generate_doc_id()})
            doc_receive_form = DocReceiveModelForm(initial={'receive_no': get_docs_no(request.user, is_secret=False)})
            parent_nav_path = "/receive"

    context = {'doc_form': doc_form, 'doc_receive_form': doc_receive_form, 'title': title,
               'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
    return render(request, 'doc_record/docreceive_form.html', context)


@login_required(login_url='/accounts/login')
def doc_receive_edit(request, id):
    doc_receive = DocReceive.objects.get(id=id)
    timezone = pytz.timezone('Asia/Bangkok')
    current_group = request.user.groups.all()[0]
    doc_old_files = DocFile.objects.filter(doc=doc_receive.doc)
    if request.method == 'POST':
        print("POST")
        user = request.user

        if 'credential' in request.path:
            doc_form = DocCredentialModelForm(request.POST, request.FILES)
        else:
            doc_form = DocModelForm(request.POST, request.FILES)
        doc_receive_form = DocReceiveModelForm(request.POST)

        if doc_form.is_valid() and doc_receive_form.is_valid():
            doc_model = doc_form.save(commit=False)
            doc_model.id = doc_receive.doc.id
            doc_model.active = 1
            doc_model.update_time = datetime.now(timezone)
            doc_model.update_by = user
            doc_model.create_time = doc_receive.doc.create_time
            doc_model.create_by = doc_receive.doc.create_by
            doc_model.save()

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
            DocTrace.objects.update_or_create(doc=doc_model, doc_status_id=1, create_by=user,
                                              action_to=current_group, action_from=current_group, done=True,
                                              defaults={'time': datetime.now(timezone)})
            for unit in send_to:
                DocTrace.objects.update_or_create(doc=doc_model, doc_status_id=2, create_by=user,
                                                  action_from=current_group, action_to=unit,
                                                  defaults={'time': datetime.now(timezone)})

            if 'credential' in request.path:
                return HttpResponseRedirect('/receive/credential')
            else:
                return HttpResponseRedirect('/receive')
    else:
        tmp_doc_date = doc_receive.doc.doc_date
        doc_receive.doc.doc_date = tmp_doc_date.replace(year=2565)
        if 'credential' in request.path:
            doc_form = DocCredentialModelForm(instance=doc_receive.doc)
            doc_receive_form = DocReceiveModelForm(instance=doc_receive)
        else:
            doc_form = DocModelForm(instance=doc_receive.doc)
            doc_receive_form = DocReceiveModelForm(instance=doc_receive)

    print(doc_old_files)
    context = {'doc_form': doc_form, 'doc_receive_form': doc_receive_form, 'doc_files': doc_old_files}
    return render(request, 'doc_record/docreceive_form.html', context)


@login_required(login_url='/accounts/login')
def doc_receive_delete(request, id):
    if request.method == "POST":
        doc_receive = get_object_or_404(DocReceive, id=id)
        units = doc_receive.send_to.all()
        for unit in units:
            doc_trace = DocTrace.objects.filter(action_to=unit, doc=doc_receive.doc)
            doc_trace.delete()
        doc_receive.delete()
    if 'credential' in request.path:
        return HttpResponseRedirect('/receive/credential')
    else:
        return HttpResponseRedirect('/receive')


def get_docs_no(user, is_secret=False):
    current_group_id = user.groups.all()[0].id
    if is_secret:
        docs = DocReceive.objects.filter(group_id=current_group_id, doc__credential__id__gt=1,
                                         doc__create_time__year=datetime.now().year)
    else:
        docs = DocReceive.objects.filter(group_id=current_group_id, doc__credential__id=1,
                                         doc__create_time__year=datetime.now().year)
    return 1 if len(docs) == 0 else docs.last().receive_no + 1
