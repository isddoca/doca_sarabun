import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


# Create your views here.
@login_required(login_url='/accounts/login')
def index(request):
    data = {
        'doc_title': "รับผิดชอบการฝึกร่วม/ผสม คอบร้าโกลด์",
        'doc_unit': "กร.ทหาร",
    }

    URL = 'http://localhost:8000/classify'
    result = requests.post(URL, data=data).json()

    context = {
        'page_title': "หน้าแรก",
        'doc_title': data.get('doc_title'),
        'doc_unit': data.get('doc_unit'),
        'doc_receive_unit': ', '.join(result['received_units']),
    }
    return render(request, 'doc_record/index.html', context)

