from django.urls import path

from .views import index, DocReceiveListView, doc_receive_add, doc_receive_edit

urlpatterns = [
    path('', index, name='receive'),
    path('receive/', DocReceiveListView.as_view(), name='receive'),
    path('receive/<int:id>/edit/', doc_receive_edit, name='receive_add'),
    path('receive/add', doc_receive_add, name='receive_add'),
]
