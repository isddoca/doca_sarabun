from datetime import date

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from django import forms

from doc_record.models import DocUrgent, DocCredential, DocReceive

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


class DocReceiveForm(forms.Form):
    receive_no = forms.CharField(label='เลขรับ', widget=forms.TextInput())
    doc_no = forms.CharField(label='เลขที่หนังสือ', widget=forms.TextInput())
    doc_date = forms.DateField(initial=date.today().strftime("%Y-%m-%d"), label='ลงวันที่',
                               widget=forms.widgets.DateInput(attrs={'type': 'date', 'format': '%Y-%m-%d'}),
                               localize=True)
    doc_urgent = forms.ChoiceField(label='ความเร่งด่วน', choices=URGENT)
    doc_credential = forms.ChoiceField(label='ระดับความลับ', choices=CREDENTIAL)
    doc_from = forms.CharField(label='จาก', widget=forms.TextInput())
    doc_to = forms.CharField(label='ถึง', widget=forms.TextInput())
    doc_title = forms.CharField(label='เรื่อง', widget=forms.TextInput())
    action = forms.CharField(label='การปฏิบัติ', widget=forms.TextInput())
    note = forms.CharField(label='หมายเหตุ', widget=forms.Textarea(), required=False)
    doc_files = forms.FileField(label='ไฟล์เอกสาร', widget=forms.ClearableFileInput(attrs={'multiple': True}),
                                required=False)

    def __init__(self, *args, user, secret, **kwargs):
        self.user = user
        self.secret = secret
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('receive_no', css_class='form-group col-md-4'),
                Column('doc_no', css_class='form-group col-md-4'),
                Column('doc_date', css_class='form-group col-md-4'),
                css_class='form-row'
            ),
            Row(
                Column('doc_urgent', css_class='form-group col-md-6'),
                Column('doc_credential', css_class='form-group col-md-6'),
            ),
            Row(
                Column('doc_from', css_class='form-group col-md-6'),
                Column('doc_to', css_class='form-group col-md-6'),
            ),
            'doc_title',
            'action',
            'note',
            'doc_files',
            Submit('submit', 'บันทึก')
        )

        self.fields['receive_no'].initial = get_credential_docs_no(user) if secret else get_normal_docs_no(user)
        self.fields['receive_no'].widget.attrs['readonly'] = True
