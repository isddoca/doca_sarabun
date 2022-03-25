import os
from datetime import date, datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from config import settings
from doc_record.forms import DocModelForm, DocCredentialModelForm, DocSendModelForm
from doc_record.models import DocFile, DocTrace, Doc, DocSend


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
        print(context['query_year'])
        return context


@method_decorator(login_required, name='dispatch')
class DocSendCredentialListView(DocSendListView):
    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        search = self.request.GET.get('year', datetime.now().year)
        return DocSend.objects.filter(group_id=current_group_id, doc__create_time__year=search,
                                         doc__credential__id__gt=1).order_by('-send_no')


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
    group_id = user.groups.all()[0].id
    if request.method == 'POST':
        if 'credential' in request.path:
            doc_form = DocCredentialModelForm(request.POST, request.FILES)
        else:
            doc_form = DocModelForm(request.POST, request.FILES)
        doc_send_form = DocSendModelForm(request.POST)

        if doc_form.is_valid() and doc_send_form.is_valid():
            doc_model = doc_form.save(commit=False)
            doc_model.id = generate_doc_id(group_id)
            doc_model.active = 1
            doc_model.create_time = datetime.now(timezone)
            doc_model.create_by = user
            doc_model.save()

            req_files = request.FILES.getlist('file')
            for f in req_files:
                DocFile.objects.create(file=f, doc=doc_model)

            doc_send_model = doc_send_form.save(commit=False)
            doc_send_model.doc = doc_model
            doc_send_model.group = user.groups.all()[0]
            doc_send_model.save()
            doc_send_form.save_m2m()

            send_to = doc_send_model.send_to.all()
            DocTrace.objects.create(doc=doc_model, doc_status_id=1, create_by=user, action_from_id=group_id, done=True,
                                    action_to_id=group_id, time=datetime.now(timezone))
            for unit in send_to:
                DocTrace.objects.create(doc=doc_model, doc_status_id=2, create_by=user, action_to=unit,
                                        action_from_id=group_id, time=datetime.now(timezone))

            if 'credential' in request.path:
                return HttpResponseRedirect('/send/credential')
            else:
                return HttpResponseRedirect('/send')
    else:
        if 'credential' in request.path:
            doc_form = DocCredentialModelForm(initial={'id': generate_doc_id(group_id)})
            doc_send_form = DocSendModelForm(initial={'send_no': get_docs_no(request.user, is_secret=True)})
        else:
            doc_form = DocModelForm(initial={'id': generate_doc_id(group_id)})
            doc_send_form = DocSendModelForm(initial={'send_no': get_docs_no(request.user, is_secret=False)})

    context = {'doc_form': doc_form, 'doc_send_form': doc_send_form}
    return render(request, 'doc_record/docsend_form.html', context)


def generate_doc_id(group_id):
    row_count = DocSend.objects.filter(doc__doc_date__year=date.today().year).count() + 1
    doc_id = "{year}-{no}".format(year=date.today().year, no=f'{row_count:06}')
    return doc_id


@login_required(login_url='/accounts/login')
def doc_send_edit(request, id):
    doc_send = DocSend.objects.get(id=id)
    timezone = pytz.timezone('Asia/Bangkok')
    current_group = request.user.groups.all()[0]
    doc_old_files = DocFile.objects.filter(doc=doc_send.doc)
    if request.method == 'POST':
        print("POST")
        user = request.user

        if 'credential' in request.path:
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
            doc_send_model.group = current_group
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
            DocTrace.objects.update_or_create(doc=doc_model, doc_status_id=1, create_by=user,
                                              action_to=current_group, action_from=current_group, done=True,
                                              defaults={'time': datetime.now(timezone)})
            for unit in send_to:
                DocTrace.objects.update_or_create(doc=doc_model, doc_status_id=2, create_by=user,
                                                  action_from=current_group, action_to=unit,
                                                  defaults={'time': datetime.now(timezone)})

            if 'credential' in request.path:
                return HttpResponseRedirect('/send/credential')
            else:
                return HttpResponseRedirect('/send')
    else:
        tmp_doc_date = doc_send.doc.doc_date
        doc_send.doc.doc_date = tmp_doc_date.replace(year=2565)
        if 'credential' in request.path:
            doc_form = DocCredentialModelForm(instance=doc_send.doc)
            doc_send_form = DocSendModelForm(instance=doc_send)
        else:
            doc_form = DocModelForm(instance=doc_send.doc)
            doc_send_form = DocSendModelForm(instance=doc_send)

    print(doc_old_files)
    context = {'doc_form': doc_form, 'doc_send_form': doc_send_form, 'doc_files': doc_old_files}
    return render(request, 'doc_record/docsend_form.html', context)


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


def get_docs_no(user, is_secret=False):
    current_group_id = user.groups.all()[0].id
    if is_secret:
        docs = DocSend.objects.filter(group_id=current_group_id, doc__credential__id__gt=1,
                                         doc__create_time__year=datetime.now().year)
    else:
        docs = DocSend.objects.filter(group_id=current_group_id, doc__credential__id=1,
                                         doc__create_time__year=datetime.now().year)
    return 1 if len(docs) == 0 else docs.last().send_no + 1

