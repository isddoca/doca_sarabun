import requests
from django.shortcuts import render

from django.http import HttpResponse


# Create your views here.

def index(request):
    data = {
        'title':"รับผิดชอบการฝึกร่วม/ผสม คอบร้าโกลด์",
        'unit':"กร.ทหาร",
    }

    URL = 'http://localhost:8000/classify'
    result = requests.post(URL, data=data).json()

    context ={
        'title':data.get('title'),
        'unit':data.get('unit'),
        'receive_unit': ', '.join(result.get('received_units')),
    }
    return render(request, 'doc_record/index.html', context)
