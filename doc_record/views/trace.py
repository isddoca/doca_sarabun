from datetime import datetime

import pythainlp.util
import pytz
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Q, Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from pythainlp import thai_strftime

from doc_record.forms import DocReceiveModelForm, DocTracePendingModelForm
from doc_record.models import DocReceive, DocTrace, DocFile
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

    if current_doc_trace.done:
        # หาจาก record สุดท้ายที่กองได้ดำเนินการล่าสุด
        current_doc_trace = DocTrace.objects.filter(action_to=current_group, doc_id=current_doc_trace.doc.id).last()
        context = {'doc_trace': current_doc_trace,
                   'old_files': doc_old_files}
        return render(request, 'doc_record/doctrace_pending_finish_view.html', context)

    if current_doc_trace.doc_status_id == 3:
        doc_receive_of_group = DocReceive.objects.get(doc=current_doc_trace.doc, group=current_group)

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
                doc_receive_form = DocReceiveModelForm(request.POST, groups_id=[current_group.id])
                doc_receive_model = doc_receive_form.save(commit=False)
                doc_receive_model.id = doc_receive_of_group.id
                doc_receive_model.receive_no = doc_receive_of_group.receive_no
                doc_receive_model.doc = doc_receive_of_group.doc
                doc_receive_model.groups = doc_receive_of_group.group
                doc_receive_model.note = doc_receive_of_group.note
                doc_receive_model.save()
                doc_receive_form.save_m2m()

                current_unit = current_doc_trace.create_by.groups.all()[0]
                pending_traces = DocTrace.objects.filter(doc=current_doc_trace.doc, done=False).exclude(
                    doc_status_id__gt=1)

                pending_unit = []
                for trace in pending_traces:
                    pending_unit.append(trace.action_to)

                done_traces = DocTrace.objects.filter(doc=current_doc_trace.doc, done=True)
                done_unit = []
                for trace in done_traces:
                    done_unit.append(trace.action_to)

                send_to = doc_receive_model.send_to.all()
                for send_unit in send_to:
                    if send_unit != current_unit and send_unit not in pending_unit and send_unit not in done_unit:  # exclude current unit
                        doc_trace, is_create = DocTrace.objects.update_or_create(doc=current_doc_trace.doc,
                                                                                 doc_status_id=2,
                                                                                 create_by=user,
                                                                                 action_from=current_group,
                                                                                 action_to=send_unit,
                                                                                 done=False,
                                                                                 defaults={
                                                                                     'time': datetime.now(
                                                                                         timezone)})

                        if is_create:  # เตือนเฉพาะหน่วยที่เพิ่มใหม่เท่านั้น
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

    context = {'doc_trace_form': doc_trace_form, 'doc_receive_form': doc_receive_form, 'doc_trace': current_doc_trace,
               'old_files': doc_old_files}
    return render(request, 'doc_record/doctrace_pending_view.html', context)


@login_required(login_url='/accounts/login')
def doc_dashboard(request):
    today_th = thai_strftime(datetime.now(), "%0d/%0m/%Y")
    query_date = request.GET.get('date', today_th)
    query_time = request.GET.get('time', "allday")

    split_date = query_date.split('/')
    ce = int(split_date[2]) - 543
    split_date[2] = str(ce)
    date = "-".join(split_date[::-1])
    time_range = []

    match query_time:
        case "allday":
            time_range = [date + " 00:00:00", date + " 23:59:59"]
        case "morning":
            time_range = [date + " 09:00:00", date + " 12:00:00"]
        case "afternoon":
            time_range = [date + " 13:00:00", date + " 16:00:00"]
    print(time_range)

    current_group = request.user.groups.all().first()
    normal_urgent_count = DocTrace.objects.order_by("action_to").values('action_to').annotate(
        doc_count=Count("action_to", filter=Q(action_from=current_group, doc__urgent__id=1, doc_status_id=2,
                                              time__range=time_range)))
    fast_urgent_count = DocTrace.objects.order_by("action_to").values('action_to').annotate(
        doc_count=Count("action_to", filter=Q(action_from=current_group, doc__urgent__id=2, doc_status_id=2,
                                              time__range=time_range)))
    faster_urgent_count = DocTrace.objects.order_by("action_to").values('action_to').annotate(
        doc_count=Count("action_to", filter=Q(action_from=current_group, doc__urgent__id=3, doc_status_id=2,
                                              time__range=time_range)))
    fastest_urgent_count = DocTrace.objects.order_by("action_to").values('action_to').annotate(
        doc_count=Count("action_to", filter=Q(action_from=current_group, doc__urgent__id=4, doc_status_id=2,
                                              time__range=time_range)))
    normal_secret_count = DocTrace.objects.order_by("action_to").values('action_to').annotate(
        doc_count=Count("action_to", filter=Q(action_from=current_group, doc__credential__id=1, doc_status_id=2,
                                              time__range=time_range)))
    high_secret_count = DocTrace.objects.order_by("action_to").values('action_to').annotate(
        doc_count=Count("action_to", filter=Q(action_from=current_group, doc__credential__id=2, doc_status_id=2,
                                              time__range=time_range)))
    higher_secret_count = DocTrace.objects.order_by("action_to").values('action_to').annotate(
        doc_count=Count("action_to", filter=Q(action_from=current_group, doc__credential__id=3, doc_status_id=2,
                                              time__range=time_range)))
    highest_secret_count = DocTrace.objects.order_by("action_to").values('action_to').annotate(
        doc_count=Count("action_to", filter=Q(action_from=current_group, doc__credential__id=4, doc_status_id=2,
                                              time__range=time_range)))

    all_groups_label = list(normal_urgent_count.values_list("action_to__name", flat=True))
    normal_urgent_count_values = list(normal_urgent_count.values_list("doc_count", flat=True))
    fast_urgent_count_values = list(fast_urgent_count.values_list("doc_count", flat=True))
    faster_urgent_count_values = list(faster_urgent_count.values_list("doc_count", flat=True))
    fastest_urgent_count_values = list(fastest_urgent_count.values_list("doc_count", flat=True))
    normal_secret_count_values = list(normal_secret_count.values_list("doc_count", flat=True))
    high_secret_count_values = list(high_secret_count.values_list("doc_count", flat=True))
    higher_secret_count_values = list(higher_secret_count.values_list("doc_count", flat=True))
    highest_secret_count_values = list(highest_secret_count.values_list("doc_count", flat=True))
    context = {
        "today": today_th,
        "labels": all_groups_label,
        "normal_values": normal_urgent_count_values,
        "fast_values": fast_urgent_count_values,
        "faster_values": faster_urgent_count_values,
        "fastest_values": fastest_urgent_count_values,
        "normal_cred_values": normal_secret_count_values,
        "high_cred_values": high_secret_count_values,
        "higher_cred_values": higher_secret_count_values,
        "highest_cred_values": highest_secret_count_values,
    }
    print(context)
    return render(request, 'doc_record/dashboard_view.html', context)
