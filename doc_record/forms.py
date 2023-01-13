from datetime import datetime

import django.utils.timezone
import pytz
from allauth.account.forms import SignupForm as b_form
from allauth.socialaccount.forms import SignupForm as s_form
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, User
from django.forms import ClearableFileInput
from pythainlp import thai_strftime

from doc_record.models import DocUrgent, DocCredential, DocReceive, Doc, DocTrace, DocSend, DocOrder

URGENT = DocUrgent.objects.all().values_list("id", "name")
CREDENTIAL = DocCredential.objects.all().values_list("id", "name")
CREDENTIAL_NORMAL = 1


def get_normal_docs_no(user):
    current_group_id = user.groups.all()[0].id
    normal_docs = DocReceive.objects.filter(group=current_group_id, doc__credential__id=CREDENTIAL_NORMAL)
    return 1 if len(normal_docs) == 0 else normal_docs.last().receive_no + 1


def get_credential_docs_no(user):
    current_group_id = user.groups.all()[0].id
    normal_docs = DocReceive.objects.filter(group=current_group_id, doc__credential__id_gt=CREDENTIAL_NORMAL)
    return 1 if len(normal_docs) == 0 else normal_docs.last().receive_no + 1


class ThaiDateCEField(forms.DateField):
    def to_python(self, value):
        split_date = value.split('/')
        ce = int(split_date[2]) - 543
        split_date[2] = str(ce)
        return "-".join(split_date[::-1])


class BasicSignupForm(b_form):
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects,
                                            widget=forms.SelectMultiple(
                                                attrs={'class': 'form-control selectmultiple form-select'}),
                                            label="หน่วยงาน", required=True)
    first_name = forms.CharField(max_length=50, label='ยศและชื่อ')
    last_name = forms.CharField(max_length=50, label='นามสกุล')

    def save(self, request):
        sign_up = super(BasicSignupForm, self).save(request)
        sign_up.first_name = self.cleaned_data['first_name']
        sign_up.last_name = self.cleaned_data['last_name']
        sign_up.password = make_password(self.cleaned_data['password1'])
        sign_up.groups.set(self.cleaned_data['groups'])
        sign_up.is_active = True
        sign_up.save()
        return sign_up


class SocialSignupForm(s_form):
    first_name = forms.CharField(max_length=50, label='ยศและชื่อ')
    last_name = forms.CharField(max_length=50, label='นามสกุล')
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects,
                                            widget=forms.SelectMultiple(
                                                attrs={'class': 'form-control selectmultiple form-select'}),
                                            label="หน่วยงาน", required=True)

    def save(self, request):
        sign_up = super(SocialSignupForm, self).save(request)
        sign_up.first_name = self.cleaned_data['first_name']
        sign_up.last_name = self.cleaned_data['last_name']
        sign_up.is_active = True
        sign_up.groups.set(self.cleaned_data['groups'])
        sign_up.save()
        return sign_up


class UserInfoForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects,
                                            widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
                                            label="หน่วยงาน", required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'groups']
        labels = {'first_name': 'ยศและชื่อ', 'last_name': 'นามสกุล'}


class DocModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.can_edit = kwargs.pop('can_edit')
        super(DocModelForm, self).__init__(*args, **kwargs)
        if not self.can_edit:
            self.fields['doc_no'].widget.attrs['readonly'] = True
            self.fields['doc_date'].widget.attrs['readonly'] = True
            self.fields['doc_from'].widget.attrs['readonly'] = True
            self.fields['doc_to'].widget.attrs['readonly'] = True
            self.fields['title'].widget.attrs['readonly'] = True
            self.fields['urgent'].widget.attrs['disabled'] = True
            self.fields['credential'].widget.attrs['disabled'] = True
            self.fields['file'].widget.attrs['disabled'] = True

    timezone = pytz.timezone('Asia/Bangkok')
    doc_date = ThaiDateCEField(input_formats=['%d/%m/%Y'],
                               label='ลงวันที่',
                               widget=forms.DateInput(attrs={'class': 'form-control', 'data-provide': "datepicker",
                                                             'data-date-language': "th-th"}), )
    urgent = forms.ModelChoiceField(queryset=DocUrgent.objects, empty_label=None, label='ความเร่งด่วน', required=False)
    credential = forms.ModelChoiceField(queryset=DocCredential.objects.filter(id=1), empty_label=None,
                                        label='ชั้นความลับ', required=False)
    file = forms.FileField(widget=ClearableFileInput(attrs={'multiple': True}), required=False, label='ไฟล์เอกสาร',
                           help_text='ผู้ใช้ควรอัพโหลดไฟล์ของหนังสือเข้าระบบ เพื่อให้หน่วยที่รับหนังสือสามารถนำหนังสือที่รับไปดำเนินการต่อ รวมถึงภายในกองสามารถดูรายละเอียดหนังสือย้อนหลังได้')

    class Meta:
        model = Doc
        fields = ['doc_no', 'doc_date', 'doc_from', 'doc_to', 'title', 'urgent', 'credential', 'file']
        labels = {'doc_no': 'เลขที่หนังสือ', 'doc_date': 'ลงวันที่', 'title': 'เรื่อง', 'doc_from': 'จาก',
                  'doc_to': 'ถึง'}
        widgets = {
            'title': forms.TextInput(),
        }


class DocCredentialModelForm(DocModelForm):
    credential = forms.ModelChoiceField(queryset=DocCredential.objects.filter(id__gt=1), empty_label=None,
                                        label='ชั้นความลับ')


class DocReceiveModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.groups_id = kwargs.pop('groups_id')
        super(DocReceiveModelForm, self).__init__(*args, **kwargs)
        self.fields['send_to'].queryset = Group.objects.exclude(id__in=self.groups_id).order_by('id')

    helper = FormHelper()
    helper.add_input(Submit('submit', 'บันทึก', css_class='btn-primary'))

    send_to = forms.ModelMultipleChoiceField(queryset=Group.objects,
                                             widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
                                             label="แจกจ่ายไปยัง", required=False)

    class Meta:
        model = DocReceive
        fields = ['receive_no', 'send_to', 'action', 'note']
        labels = {'receive_no': 'เลขรับ', 'action': 'การปฏิบัติ', 'note': 'หมายเหตุ'}
        widgets = {'receive_no': forms.TextInput(),
                   'note': forms.TextInput(),
                   'action': forms.TextInput()}


class DocSendModelForm(DocReceiveModelForm):
    class Meta:
        model = DocSend
        fields = ['send_no', 'send_to', 'action', 'note']
        labels = {'send_no': 'เลขส่ง', 'action': 'การปฏิบัติ', 'note': 'หมายเหตุ'}
        widgets = {'send_no': forms.TextInput(),
                   'note': forms.TextInput(),
                   'action': forms.TextInput()}


class DocOrderModelForm(forms.ModelForm):
    class Meta:
        model = DocOrder
        fields = ['order_no', 'action', 'note']
        labels = {'order_no': 'เลขคำสั่ง', 'action': 'การปฏิบัติ', 'note': 'หมายเหตุ'}
        widgets = {'order_no': forms.TextInput(),
                   'note': forms.TextInput(),
                   'action': forms.TextInput()}


class DocTracePendingModelForm(forms.ModelForm):
    class Meta:
        model = DocTrace
        fields = ['note']
        labels = {'note': 'หมายเหตุ'}
        widgets = {'note': forms.TextInput()}
