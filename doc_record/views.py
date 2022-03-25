import os
from datetime import date, datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django_filters.views import FilterView

from config import settings
from .forms import DocReceiveModelForm, DocModelForm, DocTracePendingModelForm
from .models import DocReceive, DocFile, DocTrace, Doc


@login_required(login_url='/accounts/login')
def index(request):
    return redirect('/receive/')


@method_decorator(login_required, name='dispatch')
class DocReceiveListView(FilterView):
    model = DocReceive
    template_name = 'doc_record/receive_index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        search = self.request.GET.get('year', datetime.now().year)
        print(search)
        return DocReceive.objects.filter(group_id=current_group_id, doc__create_time__year=search,
                                         doc__credential__id=1).order_by('-receive_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DocReceiveListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct().order_by('-create_time')
        print(context['query_year'])
        return context


@method_decorator(login_required, name='dispatch')
class DocTraceListView(ListView):
    model = DocTrace
    template_name = 'doc_record/trace_index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        object_list = DocTrace.objects.filter(
            Q(doc__create_by=self.request.user) | Q(action_to_id=current_group_id)).order_by('-time')
        return object_list


@method_decorator(login_required, name='dispatch')
class DocTracePendingListView(ListView):
    model = DocTrace
    template_name = 'doc_record/trace_pending_index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        object_list = DocTrace.objects.filter(action_to_id=current_group_id, done=False).exclude(
            doc_status_id=1).order_by('-time')
        return object_list


@login_required(login_url='/accounts/login')
def doc_receive_detail(request, id):
    doc_receive = DocReceive.objects.get(id=id)
    doc_old_files = DocFile.objects.filter(doc=doc_receive.doc)
    context = {'doc_receive': doc_receive, 'doc_files': doc_old_files}
    return render(request, 'doc_record/docreceive_view.html', context)


@login_required(login_url='/accounts/login')
def doc_trace_detail(request, id):
    doc_trace = DocTrace.objects.get(id=id)
    trace_status = DocTrace.objects.filter(doc_id=doc_trace.doc_id)
    context = {'doc_trace': doc_trace, 'trace_status': trace_status}
    return render(request, 'doc_record/doctrace_view.html', context)


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
            DocTrace.objects.create(doc=doc_model, doc_status_id=1, create_by=user, action_to_id=group_id,
                                    time=datetime.now(timezone))
            for unit in send_to:
                DocTrace.objects.create(doc=doc_model, doc_status_id=2, create_by=user, action_to=unit,
                                        time=datetime.now(timezone))

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


@login_required(login_url='/accounts/login')
def doc_trace_action(request, id):
    timezone = pytz.timezone('Asia/Bangkok')
    user = request.user
    group = user.groups.all()[0]
    current_doc_trace = DocTrace.objects.get(id=id)

    doc_receive_of_group = None
    if current_doc_trace.doc_status_id == 3:
        doc_receive_of_group = DocReceive.objects.get(doc=current_doc_trace.doc, group=group)

    if request.method == 'POST':
        doc_trace_form = DocTracePendingModelForm(request.POST)
        doc_receive_form = DocReceiveModelForm(request.POST)
        if doc_trace_form.is_valid():
            current_doc_trace.done = True
            current_doc_trace.save()
            doc_trace_save = doc_trace_form.save(commit=False)
            if 'reject' in doc_trace_form.data:
                DocTrace.objects.create(doc=current_doc_trace.doc, doc_status_id=3,
                                        action_to=current_doc_trace.create_by.groups.all()[0],
                                        create_by=user, time=datetime.now(timezone), note=doc_trace_save.note)
            elif 'resend' in doc_trace_form.data:
                doc_receive_model = doc_receive_form.save(commit=False)
                doc_receive_model.id = doc_receive_of_group.id
                doc_receive_model.receive_no = doc_receive_of_group.receive_no
                doc_receive_model.doc = doc_receive_of_group.doc
                doc_receive_model.group = doc_receive_of_group.group
                doc_receive_model.save()
                doc_receive_form.save_m2m()

                current_unit = current_doc_trace.create_by.groups.all()[0]
                pending_traces = DocTrace.objects.filter(doc=current_doc_trace.doc, doc_status_id=2, done=False)
                exclude_unit = []

                for trace in pending_traces:
                    exclude_unit.append(trace.action_to)
                send_to = doc_receive_model.send_to.all()
                for send_unit in send_to:
                    if send_unit != current_unit and send_unit not in exclude_unit:  # exclude current unit
                        DocTrace.objects.create(doc=current_doc_trace.doc, doc_status_id=2, create_by=user,
                                                action_to=send_unit,
                                                time=datetime.now(timezone), note=doc_trace_save.note)
            else:
                DocTrace.objects.create(doc=current_doc_trace.doc, doc_status_id=1,
                                        action_to=user.groups.all()[0],
                                        create_by=user, time=datetime.now(timezone), note=doc_trace_save.note)
                DocReceive.objects.create(doc=current_doc_trace.doc,
                                          receive_no=get_docs_no(user, current_doc_trace.doc.credential), group=group)
            return HttpResponseRedirect('/trace/pending')

    else:
        doc_trace_form = DocTracePendingModelForm(instance=current_doc_trace)
        doc_receive_form = DocReceiveModelForm(instance=doc_receive_of_group)

    context = {'doc_trace_form': doc_trace_form, 'doc_receive_form': doc_receive_form, 'doc_trace': current_doc_trace}
    return render(request, 'doc_record/doctrace_pending_view.html', context)
