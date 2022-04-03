from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth.forms import UserCreationForm
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
        splitdate = value.split('/')
        ce = int(splitdate[2]) - 543
        splitdate[2] = str(ce)
        return "-".join(splitdate[::-1])


class SignupForm(UserCreationForm):
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects,
                                            widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
                                            label="หน่วยงาน", required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'groups']
        labels = {'username': 'ชื่อผู้ใช้งาน', 'password': 'รหัสผ่าน', 'first_name': 'ยศและชื่อ',
                  'last_name': 'นามสกุล'}

    def save(self, commit=True):
        sign_up = super(SignupForm, self).save(commit=False)
        sign_up.password = make_password(self.cleaned_data['password1'])
        sign_up.is_active = True
        sign_up.save()
        self.save_m2m()
        return sign_up


class UserGroupForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects,
                                            widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
                                            label="หน่วยงาน", required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'groups']
        labels = {'first_name': 'ยศและชื่อ', 'last_name': 'นามสกุล'}


class DocModelForm(forms.ModelForm):
    doc_date = ThaiDateCEField(input_formats=['%d/%m/%Y'], initial=thai_strftime(datetime.today(), "%d/%m/%Y"),
                               label='ลงวันที่',
                               widget=forms.DateInput(attrs={'class': 'form-control', 'data-provide': "datepicker",
                                                             'data-date-language': "th-th"}))

    urgent = forms.ModelChoiceField(queryset=DocUrgent.objects, empty_label=None, label='ความเร่งด่วน', required=False)
    credential = forms.ModelChoiceField(queryset=DocCredential.objects.filter(id=1), empty_label=None,
                                        label='ชั้นความลับ', required=False)
    file = forms.FileField(widget=ClearableFileInput(attrs={'multiple': True}), required=False, label='ไฟล์เอกสาร')

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
    helper = FormHelper()
    helper.add_input(Submit('submit', 'บันทึก', css_class='btn-primary'))

    send_to = forms.ModelMultipleChoiceField(queryset=Group.objects,
                                             widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
                                             label="ส่งไปยัง", required=False)

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
