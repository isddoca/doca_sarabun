import json
from datetime import date

import environ
import requests
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from doc_record.forms import UserInfoForm
from doc_record.models import Doc, LineNotifyToken

env = environ.Env()
environ.Env.read_env()



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
        context = {'signup_form': signup_form}
        return render(request, 'doc_record/user_info_form.html', context)


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
def line_notify_callback(request):
    code = request.GET.get('code')
    client_id = env('LINE_NOTIFY_CLIENT_ID')
    client_secret = env('LINE_NOTIFY_CLIENT_SECRET')
    redirect_uri = 'http://localhost:8000/linenotify/callback'
    url = 'https://notify-bot.line.me/oauth/token'

    data = {'code': code, 'client_id': client_id, 'client_secret': client_secret, 'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'}
    r = requests.post(url, data=data)
    data = json.loads(r.text)
    social_account = SocialAccount.objects.get(user_id=request.user.id)
    LineNotifyToken.objects.create(token=data['access_token'], social_account=social_account)
    return redirect('/accounts/edit')


def generate_doc_id():
    row_count = Doc.objects.filter(doc_date__year=date.today().year).count() + 1
    doc_id = "{year}-{no}".format(year=date.today().year, no=f'{row_count:06}')
    return doc_id


def get_line_id(send_unit):
    user_of_group = User.objects.filter(groups__in=send_unit)
    line_accounts = SocialAccount.objects.filter(user__in=user_of_group)
    return line_accounts
