import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

# Create your views here.
from .models import DocReceive


@login_required(login_url='/accounts/login')
def index(request):
    return redirect('/send')


def send_index(request):

    context = {
        'page_title': "ทะเบียนหนังสือรับ",
        'doc_receives': DocReceive.objects.filter(group=request.user.groups.all()[0].id),
    }

    return render(request, 'doc_record/send_index.html', context)
