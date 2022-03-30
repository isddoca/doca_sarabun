from datetime import date

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render

from doc_record.models import Doc
from forms import SignupForm


@login_required(login_url='/accounts/login')
def index(request):
    return redirect('/receive/')


def signup(request):
    if request.method == 'POST':
        signup_form = SignupForm(request.POST)
        if signup_form.is_valid():
            sign_up = signup_form.save(commit=False)
            sign_up.password = make_password(signup_form.cleaned_data['password'])
            sign_up.save()
            signup_form.save_m2m()
            return HttpResponseRedirect('/accounts/login')
    else:
        signup_form = SignupForm()

    context = {'signup_form': signup_form}
    return render(request, 'registration/signup.html', context)


def generate_doc_id():
    row_count = Doc.objects.filter(doc_date__year=date.today().year).count() + 1
    doc_id = "{year}-{no}".format(year=date.today().year, no=f'{row_count:06}')
    return doc_id