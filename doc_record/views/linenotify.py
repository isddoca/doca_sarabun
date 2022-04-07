import json

import environ
import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from rest_framework import status
from songline import Sendline

from doc_record.models import LineNotifyToken

env = environ.Env()
environ.Env.read_env()


@login_required(login_url='/accounts/login')
def line_notify_register(request):
    client_id = env('LINE_NOTIFY_CLIENT_ID')
    state = 'test'
    redirect_uri = request.build_absolute_uri('callback')
    url = 'https://notify-bot.line.me/oauth/authorize?client_id={client_id}&scope=notify&response_type=code&state={state}&redirect_uri={redirect_uri}'.format(
        client_id=client_id, state=state, redirect_uri=redirect_uri)
    result = requests.get(url)
    print(result)
    return redirect(url)


@login_required(login_url='/accounts/login')
def line_notify_revoke(request):
    authorization = 'Bearer {token}'.format(token=LineNotifyToken.objects.get(user=request.user).token)
    url = 'https://notify-api.line.me/api/revoke'
    result = requests.post(url, headers={'Authorization': authorization})
    if status.is_success(result.status_code):
        user = request.user
        LineNotifyToken.objects.get(user=user).delete()
    return redirect('/accounts/edit')


@login_required(login_url='/accounts/login')
def line_notify_callback(request):
    code = request.GET.get('code')
    client_id = env('LINE_NOTIFY_CLIENT_ID')
    client_secret = env('LINE_NOTIFY_CLIENT_SECRET')
    redirect_uri = request.build_absolute_uri('callback')
    url = 'https://notify-bot.line.me/oauth/token'

    data = {'code': code, 'client_id': client_id, 'client_secret': client_secret, 'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'}
    result = requests.post(url, data=data)
    if status.is_success(result.status_code):
        data = json.loads(result.text)
        LineNotifyToken.objects.update_or_create(token=data['access_token'], defaults={'user': request.user})

    return redirect('/accounts/edit')


def send_doc_notify(group, doc_model, unit, url):
    users_in_unit = User.objects.filter(groups=unit)
    for user in users_in_unit:
        try:
            user_token = LineNotifyToken.objects.get(user=user)
            linenotify = Sendline(user_token.token)
            msg_template = "มีหนังสือส่งมาจาก : {send_from}\nที่ : {doc_no}\nลงวันที่ : {doc_date}\nเรื่อง : {title}\nURL : {url}"
            message = msg_template.format(send_from=group.name, doc_no=doc_model.doc_no,
                                          doc_date=doc_model.doc_date_th(),
                                          title=doc_model.title, url=url)
            linenotify.sendtext(message)
        except LineNotifyToken.DoesNotExist:
            print(user.username + " not registered line notify")
        except requests.exceptions.ConnectionError:
            print("เน็ตล่ม")


def doc_trace_notify(doc_trace, from_group, to_group, url):
    users_in_unit = None
    message = None
    doc = doc_trace.doc
    action = doc_trace.doc_status.name
    print(doc)
    print(action)
    match action:
        case "รับเอกสาร":
            users_in_unit = User.objects.filter(groups=to_group)
            msg_template = "{receive_from} ได้รับหนังสือ\nที่ : {doc_no}\nลงวันที่ : {doc_date}\nเรื่อง : {title}\nเรียบร้อยแล้ว"
            message = msg_template.format(receive_from=from_group, doc_no=doc.doc_no, doc_date=doc.doc_date_th(),
                                          title=doc.title)
            print(message)
        case "ส่งเอกสาร":
            users_in_unit = User.objects.filter(groups=to_group)
            msg_template = "มีหนังสือส่งมาจาก : {send_from}\nที่ : {doc_no}\nลงวันที่ : {doc_date}\nเรื่อง : {title}\nURL : {url}"
            message = msg_template.format(send_from=from_group, doc_no=doc.doc_no, doc_date=doc.doc_date_th(),
                                          title=doc.title, url=url)
        case "ตีกลับ":
            users_in_unit = User.objects.filter(groups=to_group)
            print(users_in_unit)
            msg_template = "มีหนังสือตีกลับจาก : {send_from}\nที่ : {doc_no}\nลงวันที่ : {doc_date}\nเรื่อง : {title}\nURL : {url}"
            message = msg_template.format(send_from=from_group, doc_no=doc.doc_no, doc_date=doc.doc_date_th(),
                                          title=doc.title, url=url)

    for user in users_in_unit:
        try:
            print(user.username)
            user_token = LineNotifyToken.objects.get(user=user)
            linenotify = Sendline(user_token.token)
            linenotify.sendtext(message)
        except LineNotifyToken.DoesNotExist:
            print(user.username + " not registered line notify")
        except requests.exceptions.ConnectionError:
            print("เน็ตล่ม")