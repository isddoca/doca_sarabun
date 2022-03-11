from datetime import date

from django.contrib.auth.models import User, Group
from django.test import TestCase

from .models import Doc


class docIdGenerator(TestCase):
    def testGenerate(self):
        n = 999999
        id = "{year}-{no}".format(year=date.today().year, no=f'{n:06}')
        self.assertEqual(id, '2022-999999')


class receiveDocTestCase(TestCase):
    def test_user(self):
        user = User.objects.create(id=1, username='0405', first_name="กรมกิจการพลเรือนทหารบก")
        group = Group.objects.create(id=1, name="กร.ทบ.")
        user.groups.add(group)
        user.save()

        user2 = User.objects.get(id=1)

        self.assertEqual(user2.username, "0405")
        self.assertEqual(user2.groups.all()[0].name, "กร.ทบ.")

        no = 1
        doc_id = "{year}-{no}".format(year=date.today().year, no=f'{no:06}')
        doc = Doc.objects.create(id=doc_id, doc_no="กห 0403/7588", doc_from="ยก.ทบ.", doc_to="กร.ทบ.", title="เรื่องใหม่", create_by=user, active=True)
        #doc.save()

        doc_test = Doc.objects.get(id=doc_id)
        self.assertEqual(doc, doc_test)
