from datetime import datetime

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Count, Q
from django.shortcuts import render
from pythainlp import thai_strftime

from doc_record.models import DocTrace, DocReceive, DocSend


@login_required(login_url='/accounts/login')
def distribute_info(request):
    today_th = thai_strftime(datetime.now(), "%0d/%0m/%Y")
    query_date = request.GET.get('date', today_th)
    query_time = request.GET.get('time', "allday")
    time_range = get_time_range(query_date, query_time)
    current_group = request.user.groups.all().first()
    context = get_count_of_distribute(current_group, time_range, today_th)
    return render(request, 'doc_record/dashboard_dist_view.html', context)


def send_receive_info(request):
    today_th = thai_strftime(datetime.now(), "%0d/%0m/%Y")
    query_date = request.GET.get('date', today_th)
    query_time = request.GET.get('time', "allday")
    time_range = get_time_range(query_date, query_time)
    current_group = request.user.groups.all().first()
    context = {"today": query_date}
    context.update(get_count_of_receive(current_group, time_range))
    context.update(get_count_of_send(current_group, time_range))
    return render(request, 'doc_record/dashboard_send_receive_view.html', context)


def all_unit_receive_info(request):
    today_day = datetime.now().day
    today_month = datetime.now().month
    today_year = datetime.now().year
    unit = Group.objects.all().values('name').order_by('id')
    all_unit_receive = DocTrace.objects.filter(time__day=today_day, time__month=today_month, time__year=today_year) \
        .values('action_to__name').annotate(total_doc=Count('action_to')).order_by('action_to')
    all_unit_received = DocTrace.objects.filter(time__day=today_day, time__month=today_month, time__year=today_year) \
        .values('action_to__name').annotate(total_doc=Count('action_to')).order_by('action_to').filter(done=1)
    all_unit_unreceive = DocTrace.objects.filter(time__day=today_day, time__month=today_month, time__year=today_year) \
        .values('action_to__name').annotate(total_doc=Count('action_to')).order_by('action_to').filter(done=0)

    context = {
        "date": thai_strftime(datetime.now(), "%d %B %Y")
    }

    if all_unit_receive:
        unit_df = pd.DataFrame(unit)
        total_df = pd.DataFrame(all_unit_receive)
        received_df = pd.DataFrame(all_unit_received)
        unreceive_df = pd.DataFrame(all_unit_unreceive)

        unit_df['a'] = unit_df.name.map(total_df.set_index('action_to__name').squeeze())
        unit_df['r'] = unit_df.name.map(received_df.set_index('action_to__name').squeeze())
        unit_df['u'] = unit_df.name.map(unreceive_df.set_index('action_to__name').squeeze())
        unit_df = unit_df.fillna(0)
        unit_df = unit_df.astype({'a': int, 'r': int, 'u': int})

        unit_df.rename(
            columns={'name': 'หน่วย', 'a': 'หนังสือเข้าทั้งหมด', 'r': 'รับแล้ว',
                     'u': 'ยังไม่รับ'},
            inplace=True)

        context.update({"df": unit_df.values.tolist()})

    return render(request, 'doc_record/dashboard_all_receive_view.html', context)

def get_time_range(query_date, query_time):
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
    return time_range


def get_count_of_distribute(current_group, time_range, today_th):
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
    return context


def get_count_of_receive(current_group, time_range):
    doc_receive_urgent_count = DocTrace.objects.order_by("doc__urgent__id").values('doc__urgent')\
        .annotate(urgent_count=Count("doc__urgent", filter=Q(action_from=current_group, doc_status_id=1,
                                                   time__range=time_range)))\
        .exclude(doc__urgent=None, doc__credential=None)
    doc_receive_credential_count = DocTrace.objects.order_by("doc__credential__id").values('doc__credential')\
        .annotate(credential_count=Count("doc__credential", filter=Q(action_from=current_group, doc_status_id=1,
                                                           time__range=time_range)))\
        .exclude(doc__urgent=None, doc__credential=None)

    urgent_label = list(doc_receive_urgent_count.values_list("doc__urgent__name", flat=True))
    credential_label = list(doc_receive_credential_count.values_list("doc__credential__name", flat=True))
    receive_urgent_counts = list(doc_receive_urgent_count.values_list("urgent_count", flat=True))
    receive_credential_counts = list(doc_receive_credential_count.values_list("credential_count", flat=True))

    context = {
        "r_urgent_label": urgent_label,
        "r_credential_label": credential_label,
        "r_urgent_receive_values": receive_urgent_counts,
        "r_credential_receive_values": receive_credential_counts,
    }
    return context


def get_count_of_send(current_group, time_range):
    doc_receive_urgent_count = DocSend.objects.order_by("doc__urgent__id").values('doc__urgent')\
        .annotate(urgent_count=Count("doc__urgent", filter=Q(group_id=current_group.id,
                                                   doc__create_time__range=time_range)))\
        .exclude(doc__credential=None).exclude(doc__urgent=None).exclude(doc__title=None)
    doc_receive_credential_count = DocSend.objects.order_by("doc__credential__id").values('doc__credential')\
        .annotate(credential_count=Count("doc__credential", filter=Q(group_id=current_group.id,
                                                           doc__create_time__range=time_range)))\
        .exclude(doc__credential=None).exclude(doc__urgent=None).exclude(doc__title=None)

    urgent_label = list(doc_receive_urgent_count.values_list("doc__urgent__name", flat=True))
    credential_label = list(doc_receive_credential_count.values_list("doc__credential__name", flat=True))
    receive_urgent_counts = list(doc_receive_urgent_count.values_list("urgent_count", flat=True))
    receive_credential_counts = list(doc_receive_credential_count.values_list("credential_count", flat=True))

    context = {
        "s_urgent_label": urgent_label,
        "s_credential_label": credential_label,
        "s_urgent_receive_values": receive_urgent_counts,
        "s_credential_receive_values": receive_credential_counts,
    }
    return context
