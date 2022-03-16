from django.urls import path

from .views import index, DocReceiveListView, doc_receive_form

urlpatterns = [
    path('', index, name='receive'),
    path('receive/', DocReceiveListView.as_view(), name='receive'),
    path('receive/add', doc_receive_form, name='receive_add'),
]
