import json

import environ
import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from rest_framework import status

from doc_record.models import LineNotifyToken

env = environ.Env()
environ.Env.read_env()


@login_required(login_url='/accounts/login')
def line_notify_register(request):
    client_id = env('LINE_NOTIFY_CLIENT_ID')
    state = 'test'
    redirect_uri = 'http://localhost:8000/linenotify/callback'
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
    redirect_uri = 'http://localhost:8000/linenotify/callback'
    url = 'https://notify-bot.line.me/oauth/token'

    data = {'code': code, 'client_id': client_id, 'client_secret': client_secret, 'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'}
    result = requests.post(url, data=data)
    data = json.loads(result.text)
    LineNotifyToken.objects.update_or_create(token=data['access_token'], defaults={'user': request.user})
    return redirect('/accounts/edit')
