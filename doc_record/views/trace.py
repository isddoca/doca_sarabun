from datetime import datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from doc_record.forms import DocReceiveModelForm, DocTracePendingModelForm, DocSendModelForm
from doc_record.models import DocReceive, DocTrace, DocFile, DocSend
from doc_record.views.linenotify import doc_trace_notify
from doc_record.views.receive import get_docs_no


@method_decorator(login_required, name='dispatch')
class DocTraceListView(ListView):
    model = DocTrace
    template_name = 'doc_record/trace_index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        object_list = DocTrace.objects.filter(
            Q(action_from_id=current_group_id) | Q(action_to_id=current_group_id)).order_by('-time')
        return object_list


@method_decorator(login_required, name='dispatch')
class DocTracePendingListView(DocTraceListView):
    template_name = 'doc_record/trace_pending_index.html'

    def get_queryset(self):
        current_group_id = self.request.user.groups.all()[0].id
        object_list = DocTrace.objects.filter(action_to_id=current_group_id, done=False).exclude(
            doc_status_id=1).order_by('-time')
        return object_list


@login_required(login_url='/accounts/login')
def doc_trace_detail(request, id):
    try:
        doc_trace = DocTrace.objects.get(id=id)
        trace_status = DocTrace.objects.filter(doc_id=doc_trace.doc_id).order_by('time')
        context = {'doc_trace': doc_trace, 'trace_status': trace_status}
        return render(request, 'doc_record/doctrace_view.html', context)
    except DocTrace.DoesNotExist:
        return render(request, 'doc_record/doctrace_view_notfound.html')


@login_required(login_url='/accounts/login')
def doc_trace_action(request, id):
    timezone = pytz.timezone('Asia/Bangkok')
    user = request.user
    current_group = user.groups.all()[0]
    current_doc_trace = DocTrace.objects.get(id=id)
    doc_old_files = DocFile.objects.filter(doc=current_doc_trace.doc)

    doc_receive_of_group = None
    doc_send_of_group = None

    if current_doc_trace.done:
        # หาจาก record สุดท้ายที่กองได้ดำเนินการล่าสุด
        current_doc_trace = DocTrace.objects.filter(action_from=current_group, doc_id=current_doc_trace.doc.id).last()
        context = {'doc_trace': current_doc_trace,
                   'old_files': doc_old_files}
        return render(request, 'doc_record/doctrace_pending_finish_view.html', context)

    from_receive = False
    from_send = False
    if current_doc_trace.doc_status_id == 3:
        try:
            doc_receive_of_group = DocReceive.objects.get(doc=current_doc_trace.doc, group=current_group)
            from_receive = True
        except DocReceive.DoesNotExist:
            doc_send_of_group = DocSend.objects.get(doc=current_doc_trace.doc, group=current_group)
            from_send = True

    if request.method == 'POST':
        doc_trace_form = DocTracePendingModelForm(request.POST)
        if doc_trace_form.is_valid():
            current_doc_trace.done = True
            current_doc_trace.save()
            doc_trace_save = doc_trace_form.save(commit=False)
            if 'reject' in doc_trace_form.data:
                doc_trace = DocTrace.objects.create(doc=current_doc_trace.doc, doc_status_id=3,
                                                    action_from=current_group,
                                                    action_to=current_doc_trace.create_by.groups.all()[0],
                                                    create_by=user, time=datetime.now(timezone),
                                                    note=doc_trace_save.note)
                url = request.build_absolute_uri('/trace/pending/' + str(doc_trace.pk))
                doc_trace_notify(doc_trace, current_group, current_doc_trace.action_from, url)
            elif 'resend' in doc_trace_form.data:
                if from_receive:
                    doc_receive_model = save_doc_receive(current_group, doc_receive_of_group, request)
                elif from_send:
                    doc_send_model = save_doc_send(current_group, doc_send_of_group, request)

                current_unit = current_doc_trace.create_by.groups.all()[0]
                reject_traces = DocTrace.objects.filter(doc=current_doc_trace.doc, doc_status_id=3)

                reject_unit = []
                for trace in reject_traces:
                    reject_unit.append(trace.action_from)

                done_traces = DocTrace.objects.filter(doc=current_doc_trace.doc, done=True)
                done_unit = []
                for trace in done_traces:
                    done_unit.append(trace.action_to)

                if from_receive:
                    send_to = doc_receive_model.send_to.all()
                else:
                    send_to = doc_send_model.send_to.all()
                for send_unit in send_to:
                    if send_unit != current_unit or send_unit in reject_unit or send_unit not in done_unit:  # exclude current unit
                        print(send_unit)
                        doc_trace, is_create = DocTrace.objects.update_or_create(doc=current_doc_trace.doc,
                                                                                 doc_status_id=2,
                                                                                 action_from=current_group,
                                                                                 action_to=send_unit,
                                                                                 defaults={
                                                                                     'time': datetime.now(timezone),
                                                                                     'done': False,
                                                                                     'create_by': user})

                        if is_create:  # เตือนเฉพาะหน่วยที่เพิ่มใหม่เท่านั้น
                            print("send_chat_to "+send_unit)
                            url = request.build_absolute_uri('/trace/pending/' + str(doc_trace.pk))
                            doc_trace_notify(doc_trace, current_group, send_unit, url)
            else:
                doc_trace = DocTrace.objects.create(doc=current_doc_trace.doc, doc_status_id=1, action_to=current_group,
                                                    action_from=current_group,
                                                    create_by=user, time=datetime.now(timezone),
                                                    note=doc_trace_save.note,
                                                    done=True)

                doc_trace_notify(doc_trace, current_group, current_doc_trace.action_from, None)
                DocReceive.objects.create(doc=current_doc_trace.doc,
                                          receive_no=get_docs_no(user, current_doc_trace.doc.is_secret()),
                                          group=current_group)
            return HttpResponseRedirect('/trace/pending')

    else:
        doc_trace_form = DocTracePendingModelForm(instance=current_doc_trace)
        doc_receive_form = DocReceiveModelForm(instance=doc_receive_of_group, groups_id=[current_group.id])
        doc_send_form = DocSendModelForm(instance=doc_send_of_group, groups_id=[current_group.id])

    context = {'doc_trace_form': doc_trace_form, 'doc_trace': current_doc_trace,
               'old_files': doc_old_files}
    if from_receive:
        context.update({'doc_action_form': doc_receive_form})
    else:
        context.update({'doc_action_form': doc_send_form})
    return render(request, 'doc_record/doctrace_pending_view.html', context)


def save_doc_send(current_group, doc_send_of_group, request):
    doc_send_form = DocSendModelForm(request.POST, groups_id=[current_group.id])
    doc_send_model = doc_send_form.save(commit=False)
    doc_send_model.id = doc_send_of_group.id
    doc_send_model.send_no = doc_send_of_group.send_no
    doc_send_model.doc = doc_send_of_group.doc
    doc_send_model.group = doc_send_of_group.group
    doc_send_model.note = doc_send_of_group.note
    doc_send_model.save()
    doc_send_form.save_m2m()
    return doc_send_model


def save_doc_receive(current_group, doc_receive_of_group, request):
    doc_receive_form = DocReceiveModelForm(request.POST, groups_id=[current_group.id])
    doc_receive_model = doc_receive_form.save(commit=False)
    doc_receive_model.id = doc_receive_of_group.id
    doc_receive_model.receive_no = doc_receive_of_group.receive_no
    doc_receive_model.doc = doc_receive_of_group.doc
    doc_receive_model.group = doc_receive_of_group.group
    doc_receive_model.note = doc_receive_of_group.note
    doc_receive_model.save()
    doc_receive_form.save_m2m()
    return doc_receive_model
