from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from doc_record.models import Doc


@login_required(login_url='/accounts/login')
def index(request):
    return redirect('/receive/')


def generate_doc_id():
    row_count = Doc.objects.filter(doc_date__year=date.today().year).count() + 1
    doc_id = "{year}-{no}".format(year=date.today().year, no=f'{row_count:06}')
    return doc_id