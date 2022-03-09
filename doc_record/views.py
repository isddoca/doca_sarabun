import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# Create your views here.
@login_required(login_url='/accounts/login')
def index(request):
    data = {
        'title': "รับผิดชอบการฝึกร่วม/ผสม คอบร้าโกลด์",
        'unit': "กร.ทหาร",
    }

    URL = 'http://localhost:8000/classify'
    result = requests.post(URL, data=data).json()

    context = {
        'title': data.get('title'),
        'unit': data.get('unit'),
        'receive_unit': ', '.join(result['received_units']),
    }
    return render(request, 'doc_record/index.html', context)


def login(request):
    return render(request, 'doc_record/login.html')
