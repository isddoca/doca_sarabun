from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView

from form import DocReceiveForm
from .models import DocReceive, Doc


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
        object_list = DocReceive.objects.filter(group=current_group_id, doc__doc_date__year=date.today().year + 543,
                                                doc__credential__id=1).order_by('-receive_no')
        return object_list


@login_required(login_url='/accounts/login')
def doc_receive_form(request):
    if request.method == 'POST':
        form = DocReceiveForm(request.POST, user=request.user, secret=False)
        if form.is_valid():
            group_id = form.user.groups.all()[0].id
            row_count = DocReceive.objects.filter(group_id=group_id,
                                                  doc__doc_date__year=date.today().year + 543,
                                                  doc__credential__id=1).count()
            doc_id = "{year}-{no}".format(year=date.today().year, no=f'{row_count:06}')
            doc = Doc.objects.create(id=doc_id, doc_no=form.cleaned_data['doc_no'],
                                     doc_date=form.cleaned_data['doc_date'],
                                     doc_from=form.cleaned_data['doc_from'], doc_to=form.cleaned_data['doc_to'],
                                     urgent_id=form.cleaned_data['doc_urgent'],
                                     credential_id=form.cleaned_data['doc_credential'], active=True,
                                     title=form.cleaned_data['doc_title'],
                                     create_by_id=form.user.id, create_time=datetime.now())
            doc.save()

            doc_receive = DocReceive.objects.create(receive_no=form.cleaned_data['receive_no'],
                                                    doc_id=doc.id,
                                                    group_id=group_id,
                                                    action=form.cleaned_data['action'],
                                                    note=form.cleaned_data['note'])
            doc_receive.save()
            return HttpResponseRedirect('/receive')


    else:
        form = DocReceiveForm(user=request.user, secret=False)
    return render(request, 'doc_record/docreceive_form.html', {'form': form})


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
