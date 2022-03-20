from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth.models import Group
from pythainlp import thai_strftime

from doc_record.models import DocUrgent, DocCredential, DocReceive, Doc

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


class DocModelForm(forms.ModelForm):
    helper = FormHelper()

    doc_date = ThaiDateCEField(input_formats=['%d/%m/%Y'], initial=thai_strftime(datetime.today(), "%d/%m/%Y"),
                               label='ลงวันที่',
                               widget=forms.DateInput(attrs={'class': 'form-control', 'data-provide': "datepicker",
                                                             'data-date-language': "th-th"}))

    urgent = forms.ModelChoiceField(queryset=DocUrgent.objects, empty_label=None, label='ความเร่งด่วน')
    credential = forms.ModelChoiceField(queryset=DocCredential.objects, empty_label=None, label='ชั้นความลับ')

    class Meta:
        model = Doc
        fields = ['doc_no', 'doc_date', 'doc_from', 'doc_to', 'title', 'urgent', 'credential']
        labels = {'doc_no': 'เลขที่หนังสือ', 'doc_date': 'ลงวันที่', 'title': 'เรื่อง', 'doc_from': 'จาก',
                  'doc_to': 'ถึง'}
        widgets = {
            'title': forms.TextInput(),
        }


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
