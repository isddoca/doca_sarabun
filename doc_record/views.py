from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView

from .models import DocReceive


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
        object_list = DocReceive.objects.filter(group=current_group_id, doc__doc_date__year=2565)
        return object_list


@method_decorator(login_required, name='dispatch')
class DocReceiveCreateView(CreateView):
    model = DocReceive
    fields = [
        "receive_no",
        "action",
        "note",
    ]

    def form_valid(self, form):
        print(form)
        # doc = Doc()
        # self.object - form.save(commit=False)


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





