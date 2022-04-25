import json
from datetime import date

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from doc_record.forms import UserInfoForm
from doc_record.models import Doc, LineNotifyToken, DocTrace


@login_required(login_url='/accounts/login')
def account_init(request):
    groups = request.user.groups.all()
    if groups:
        return redirect('/receive/')
    elif request.method == 'POST':
        signup_form = UserInfoForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save(commit=False)
            user.id = request.user.id
            user.username = request.user.username
            user.password = request.user.password
            user.save()
            signup_form.save_m2m()
        return redirect('/receive/')
    else:
        signup_form = UserInfoForm(instance=request.user)
        context = {'signup_form': signup_form}
        return render(request, 'account/init_group.html', context)


@login_required(login_url='/accounts/login')
def user_info_edit(request):
    if request.method == 'POST':
        signup_form = UserInfoForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save(commit=False)
            user.id = request.user.id
            user.username = request.user.username
            user.password = request.user.password
            user.save()
            signup_form.save_m2m()
        return redirect('/receive/')
    else:
        signup_form = UserInfoForm(instance=request.user)
        try:
            linenotify_status = LineNotifyToken.objects.get(user=request.user)
        except LineNotifyToken.DoesNotExist:
            linenotify_status = None
        context = {'signup_form': signup_form, 'notify_status': linenotify_status}
        return render(request, 'doc_record/user_info_form.html', context)


@csrf_exempt
def fulfillment(request):
    # build a request object
    req = json.loads(request.body)
    print(req)
    # get action from json
    action = req.get('queryResult').get('action')
    param = req.get('queryResult').get('parameters')

    match action:
        case "track_document":
            doc_no = param.get('doc_no')
            if doc_no == '':
                fulfillment_txt = {'fulfillmentText': 'กรุณาแจ้งเลขที่หนังสือคำสั่งด้วยครับ'}
            else:
                doc_trace = DocTrace.objects.filter(doc__doc_no=doc_no).order_by('time')
                if doc_trace:
                    detail = f"ที่ : {doc_trace[0].doc.doc_no}\nเรื่อง : {doc_trace[0].doc.title}\n\nสถานะหนังสือ :\n"
                    for trace in doc_trace:
                        if trace.action_from == trace.action_to:
                            detail += f'{trace.action_from} รับเอกสารเข้าระบบเมื่อ {trace.time_th()}\n'
                        else:
                            detail += f'{trace.action_from} {trace.doc_status.name}ไปยัง {trace.action_to} ' \
                                      f'เมื่อ {trace.time_th()}\n'

                    fulfillment_txt = {'fulfillmentText': detail}
                else:
                    fulfillment_txt = {'fulfillmentText': 'ไม่พบข้อมูลหนังสือ/คำสั่งนี้ครับ'}
        case _:
            fulfillment_txt = {'fulfillmentText': 'This is Django test response from webhook. 3'}
    return JsonResponse(fulfillment_txt, safe=False)


def trace_answer(doc_no):
    if doc_no == '':
        fulfillment_txt = {'fulfillmentText': 'กรุณาแจ้งเลขที่หนังสือคำสั่งด้วยครับ'}
    else:
        doc_trace = DocTrace.objects.filter(doc__doc_no=doc_no).order_by('time')
        if doc_trace:
            detail = f"ที่ : {doc_trace[0].doc.doc_no}\nเรื่อง : {doc_trace[0].doc.title}\n\nสถานะหนังสือ :\n"
            for trace in doc_trace:
                if trace.action_from == trace.action_to:
                    detail += f'{trace.action_from} รับเอกสารเข้าระบบเมื่อ {trace.time_th()}\n'
                else:
                    detail += f'{trace.action_from} {trace.doc_status.name}ไปยัง {trace.action_to} เมื่อ {trace.time_th()}\n'

            fulfillment_txt = {'fulfillmentText': detail}
        else:
            fulfillment_txt = {'fulfillmentText': 'ไม่พบข้อมูลหนังสือ/คำสั่งนี้ครับ'}
    return fulfillment_txt


def generate_doc_id():
    docs_record = Doc.objects.filter(doc_date__year=date.today().year).last()
    latest_id = int(docs_record.id[5:])+1 if docs_record else 1
    doc_id = "{year}-{no}".format(year=date.today().year, no=f'{latest_id:06}')
    return doc_id


def get_line_id(send_unit):
    user_of_group = User.objects.filter(groups__in=send_unit)
    line_accounts = SocialAccount.objects.filter(user__in=user_of_group)
    return line_accounts
