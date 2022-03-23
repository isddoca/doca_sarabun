import os
from datetime import date, datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, UpdateView, DeleteView

from config import settings
from .forms import DocReceiveModelForm, DocModelForm
from .models import DocReceive, DocFile, DocTrace


@login_required(login_url='/accounts/login')
def index(request):
    return redirect('/receive/')


@method_decorator(login_required, name='dispatch')
class DocReceiveListView(ListView):
    model = DocReceive
    template_name = 'doc_record/receive_index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        object_list = DocReceive.objects.filter(group_id=current_group_id, doc__doc_date__year=2022,
                                                doc__credential__id=1).order_by('-receive_no')
        return object_list


@method_decorator(login_required, name='dispatch')
class DocTraceListView(ListView):
    model = DocTrace
    template_name = 'doc_record/trace_index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        object_list = DocTrace.objects.filter(
            Q(create_by=self.request.user) | Q(action_to_id=current_group_id)).order_by('-time')
        return object_list


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
    if request.method == 'POST':
        doc_form = DocModelForm(request.POST, request.FILES)
        doc_receive_form = DocReceiveModelForm(request.POST)

        if doc_form.is_valid() and doc_receive_form.is_valid():
            doc_model = doc_form.save(commit=False)
            doc_model.id = generate_doc_id(group_id)
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
            DocTrace.objects.create(doc=doc_model, doc_status_id=1, create_by=user, action_to_id=group_id)
            for unit in send_to:
                DocTrace.objects.create(doc=doc_model, doc_status_id=2, create_by=user, action_to=unit)

            DocTrace.objects.create(doc=doc_model, doc_status_id=1, create_by=user)
            if doc_receive_model.send_to.all():
                for unit in doc_receive_model.send_to.all():
                    DocTrace.objects.create(doc=doc_model, doc_status_id=2, create_by=user, action_to=unit)

            return HttpResponseRedirect('/receive')
    else:
        doc_form = DocModelForm(initial={'id': generate_doc_id(group_id)})
        doc_receive_form = DocReceiveModelForm(initial={'receive_no': get_docs_no(request.user)})

    context = {'doc_form': doc_form, 'doc_receive_form': doc_receive_form}
    return render(request, 'doc_record/docreceive_form.html', context)


def generate_doc_id(group_id):
    row_count = DocReceive.objects.filter(doc__doc_date__year=date.today().year).count() + 1
    doc_id = "{year}-{no}".format(year=date.today().year, no=f'{row_count:06}')
    return doc_id


@login_required(login_url='/accounts/login')
def doc_receive_edit(request, id):
    doc_receive = DocReceive.objects.get(id=id)
    timezone = pytz.timezone('Asia/Bangkok')
    doc_old_files = DocFile.objects.filter(doc=doc_receive.doc)
    if request.method == 'POST':
        print("POST")
        user = request.user
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
            doc_receive_model.group = user.groups.all()[0]
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

            return HttpResponseRedirect('/receive')
    else:
        tmp_doc_date = doc_receive.doc.doc_date
        doc_receive.doc.doc_date = tmp_doc_date.replace(year=2565)
        doc_form = DocModelForm(instance=doc_receive.doc)
        doc_receive_form = DocReceiveModelForm(instance=doc_receive)

    print(doc_old_files)
    context = {'doc_form': doc_form, 'doc_receive_form': doc_receive_form, 'doc_files': doc_old_files}
    return render(request, 'doc_record/docreceive_form.html', context)


def get_docs_no(user, is_secret=False):
    current_group_id = user.groups.all()[0].id
    if is_secret:
        docs = DocReceive.objects.filter(group_id=current_group_id, doc__credential__id__gt=1,
                                         doc__create_time__year=datetime.now().year)
    else:
        docs = DocReceive.objects.filter(group_id=current_group_id, doc__credential__id=1,
                                         doc__create_time__year=datetime.now().year)
    return 1 if len(docs) == 0 else docs.last().receive_no + 1


class DocReceiveDetailView(DetailView):
    model = DocReceive


class DocReceiveUpdateView(UpdateView):
    model = DocReceive
    fields = [
        "receive_no"
        "doc"
        "action"
        "note"
    ]


class DocReceiveDeleteView(DeleteView):
    model = DocReceive
    success_url = "/receive"
