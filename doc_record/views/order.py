import os
from datetime import datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from config import settings
from doc_record.forms import DocModelForm, DocOrderModelForm
from doc_record.models import DocFile, Doc, DocOrder
from doc_record.views.base import generate_doc_id


@method_decorator(login_required, name='dispatch')
class DocOrderListView(ListView):
    model = DocOrder
    template_name = 'doc_record/order_index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        search = self.request.GET.get('year', datetime.now().year)
        return DocOrder.objects.filter(doc__create_time__year=search, specific=False).order_by('-order_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DocOrderListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct()
        context['title'] = "คำสั่ง"
        context['add_button'] = "ลงทะเบียนคำสั่ง"
        context['add_path'] = "add"
        return context


@method_decorator(login_required, name='dispatch')
class DocOrderSpecificListView(DocOrderListView):
    def get_queryset(self):
        search = self.request.GET.get('year', datetime.now().year)
        return DocOrder.objects.filter(doc__create_time__year=search, specific=True).order_by('-order_no')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DocOrderSpecificListView, self).get_context_data(**kwargs)
        context['query_year'] = Doc.objects.dates('create_time', 'year').distinct()
        context['title'] = "คำสั่ง (เฉพาะ)"
        context['add_button'] = "ลงทะเบียนคำสั่ง (เฉพาะ)"
        context['add_path'] = "specific/add"
        context['edit_path'] = "specific/"
        return context


@login_required(login_url='/accounts/login')
def doc_order_detail(request, id):
    is_specific = 'specific' in request.path

    if is_specific:
        title = "รายละเอียดคำสั่ง (เฉพาะ)"
        parent_nav_title = "ทะเบียนคำสั่ง (เฉพาะ)"
        parent_nav_path = "/order/specific"
    else:
        title = "รายละเอียดคำสั่ง"
        parent_nav_title = "ทะเบียนคำสั่ง "
        parent_nav_path = "/order"

    doc_order = DocOrder.objects.get(id=id)
    doc_old_files = DocFile.objects.filter(doc=doc_order.doc)
    context = {'doc_order': doc_order, 'doc_files': doc_old_files, 'title': title,
               'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
    return render(request, 'doc_record/docorder_view.html', context)


@login_required(login_url='/accounts/login')
def doc_order_add(request):
    timezone = pytz.timezone('Asia/Bangkok')
    user = request.user
    current_group = user.groups.all()[0]

    is_specific = 'specific' in request.path

    parent_nav_title = "ทะเบียนคำสั่ง"
    parent_nav_path = "/order"
    title = "ลงทะเบียนคำสั่ง"
    if request.method == 'POST':
        doc_form = DocModelForm(request.POST, request.FILES, can_edit=True)
        doc_order_form = DocOrderModelForm(request.POST)
        if doc_form.is_valid() and doc_order_form.is_valid():
            doc_model = doc_form.save(commit=False)
            doc_model.id = request.POST["doc_id"]
            doc_model.active = 1
            doc_model.create_time = datetime.now(timezone)
            doc_model.create_by = user
            doc_model.save()

            req_files = request.FILES.getlist('file')
            for f in req_files:
                DocFile.objects.create(file=f, doc=doc_model)

            doc_order = doc_order_form.save(commit=False)
            doc_order.id = request.POST["order_id"]
            doc_order.doc = doc_model
            doc_order.specific = is_specific
            doc_order.issue_by = current_group
            doc_order.save()

            if 'specific' in request.path:
                return HttpResponseRedirect('/order/specific')
            else:
                return HttpResponseRedirect('/order')
    else:
        order_no = get_order_no(is_specific=is_specific)
        doc = Doc.objects.create(id=generate_doc_id(), doc_no=get_doc_no(is_specific), active=True, create_by=user,
                                 create_time=datetime.now(timezone))
        doc.save()
        doc_order = DocOrder.objects.create(order_no=order_no, doc=doc, specific=is_specific, issue_by=current_group)
        doc_order.save()

        doc_form = DocModelForm(instance=doc, can_edit=True)
        doc_order_form = DocOrderModelForm(instance=doc_order)
        if is_specific:
            title = "ลงทะเบียนคำสั่ง (เฉพาะ)"
            parent_nav_title = "ทะเบียนคำสั่ง (เฉพาะ)"
            parent_nav_path = "/order/specific"
        else:
            parent_nav_path = "/order"

        context = {'doc_id': doc.id, 'order_id': doc_order.id, 'doc_form': doc_form,
                   'doc_order_form': doc_order_form, 'title': title, 'parent_nav_title': parent_nav_title,
                   'parent_nav_path': parent_nav_path}
        return render(request, 'doc_record/docorder_form.html', context)


@login_required(login_url='/accounts/login')
def doc_order_edit(request, id):
    doc_order = DocOrder.objects.get(id=id)
    timezone = pytz.timezone('Asia/Bangkok')
    current_group = request.user.groups.all()[0]

    is_specific = 'specific' in request.path
    can_edit_doc = current_group in doc_order.doc.create_by.groups.all()

    parent_nav_title = "ทะเบียนคำสั่ง"
    parent_nav_path = "/order"
    title = "ลงทะเบียนคำสั่ง"

    doc_old_files = DocFile.objects.filter(doc=doc_order.doc)
    if request.method == 'POST':
        print("POST")
        user = request.user

        doc_form = DocModelForm(request.POST, request.FILES, can_edit=can_edit_doc)
        doc_order_form = DocOrderModelForm(request.POST)

        if doc_form.is_valid() and doc_order_form.is_valid():
            if can_edit_doc:
                doc = doc_form.save(commit=False)
                doc.id = doc_order.doc.id
                doc.active = 1
                doc.update_time = datetime.now(timezone)
                doc.update_by = user
                doc.create_time = doc_order.doc.create_time
                doc.create_by = doc_order.doc.create_by
                doc.save()
            else:
                doc = doc_order.doc

            upd_doc_order = doc_order_form.save(commit=False)
            upd_doc_order.id = doc_order.id
            upd_doc_order.doc = doc
            upd_doc_order.specific = is_specific
            upd_doc_order.issue_by = user.groups.all()[0]
            upd_doc_order.save()

            # ถ้าไม่มีไฟล์อัพเดท ไม่ต้องลบ ถ้ามีให้ลบแล้วเพิ่มใหม่
            files = request.FILES.getlist('file')
            if len(files) > 0:
                for f in doc_old_files:
                    os.remove(os.path.join(settings.MEDIA_ROOT, f.file.name))
                    f.delete()

                for f in files:
                    DocFile.objects.create(file=f, doc=doc)

            if is_specific:
                return HttpResponseRedirect('/order/specific')
            else:
                return HttpResponseRedirect('/order')
    else:
        tmp_doc_date = doc_order.doc.doc_date
        doc_order.doc.doc_date = tmp_doc_date.replace(year=tmp_doc_date.year + 543)
        doc_form = DocModelForm(instance=doc_order.doc, can_edit=can_edit_doc)
        doc_order_form = DocOrderModelForm(instance=doc_order)
        if is_specific:
            title = "ลงทะเบียนคำสั่ง (เฉพาะ)"
            parent_nav_title = "ทะเบียนคำสั่ง (เฉพาะ)"
            parent_nav_path = "/order/specific"

    context = {'doc_form': doc_form, 'doc_order_form': doc_order_form, 'doc_files': doc_old_files, 'title': title,
               'parent_nav_title': parent_nav_title, 'parent_nav_path': parent_nav_path}
    return render(request, 'doc_record/docorder_form.html', context)


@login_required(login_url='/accounts/login')
def doc_order_delete(request, id):
    is_specific = 'specific' in request.path
    if request.method == "POST":
        doc_order = get_object_or_404(DocOrder, id=id)
        doc_order.delete()
    if is_specific:
        return HttpResponseRedirect('/order/specific')
    else:
        return HttpResponseRedirect('/order')


def get_order_no(is_specific=False):
    docs = DocOrder.objects.filter(specific=is_specific, doc__create_time__year=datetime.now().year).order_by(
        'order_no')
    return 1 if len(docs) == 0 else docs.last().order_no + 1


def get_doc_no(is_specific=False):
    return str(get_order_no(is_specific)) + "/" + str(int(datetime.now().year) + 543)
