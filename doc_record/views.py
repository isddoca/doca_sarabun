from datetime import date, datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, UpdateView, DeleteView

from .forms import DocReceiveModelForm, DocModelForm
from .models import DocReceive, DocTrace


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
        object_list = DocReceive.objects.filter(group=current_group_id, doc__doc_date__year=2022,
                                                doc__credential__id=1).order_by('-receive_no')
        return object_list


@login_required(login_url='/accounts/login')
def doc_receive_form(request):
    timezone = pytz.timezone('Asia/Bangkok')
    if request.method == 'POST':
        user = request.user
        group_id = user.groups.all()[0].id
        row_count = DocReceive.objects.filter(group_id=group_id,
                                              doc__doc_date__year=date.today().year,
                                              doc__credential__id=1).count() + 1
        doc_id = "{year}-{no}".format(year=date.today().year, no=f'{row_count:06}')
        doc_form = DocModelForm(request.POST)
        doc_receive_form = DocReceiveModelForm(request.POST)

        if doc_form.is_valid() and doc_receive_form.is_valid():
            doc_model = doc_form.save(commit=False)
            doc_model.id = doc_id
            doc_model.active = 1
            doc_model.create_time = datetime.now(timezone)
            doc_model.create_by = user
            print(doc_model)
            doc_model.save()

            doc_receive_model = doc_receive_form.save(commit=False)
            doc_receive_model.doc = doc_model
            doc_receive_model.group = user.groups.all()[0]
            doc_receive_model.save()

            doc_trace_model = DocTrace(doc_id=doc_id, doc_status_id=1, time=datetime.now(tz=timezone),
                                       create_by=user, action_to=user)
            doc_trace_model.save()

            return HttpResponseRedirect('/receive')

    else:
        doc_form = DocModelForm
        doc_receive_form = DocReceiveModelForm(initial={'receive_no': get_docs_no(request.user)})

    context = {'doc_form': doc_form, 'doc_receive_form': doc_receive_form}
    return render(request, 'doc_record/docreceive_form.html', context)


def get_docs_no(user, is_secret=False):
    current_group_id = user.groups.all()[0].id
    if is_secret:
        docs = DocReceive.objects.filter(group=current_group_id, doc__credential__id__gt=1)
    else:
        docs = DocReceive.objects.filter(group=current_group_id, doc__credential__id=1)
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
