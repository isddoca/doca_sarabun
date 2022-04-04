import json
from datetime import date

import environ
import requests
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from rest_framework import status

from doc_record.forms import UserInfoForm
from doc_record.models import Doc, LineNotifyToken


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


def generate_doc_id():
    row_count = Doc.objects.filter(doc_date__year=date.today().year).count() + 1
    doc_id = "{year}-{no}".format(year=date.today().year, no=f'{row_count:06}')
    return doc_id


def get_line_id(send_unit):
    user_of_group = User.objects.filter(groups__in=send_unit)
    line_accounts = SocialAccount.objects.filter(user__in=user_of_group)
    return line_accounts
