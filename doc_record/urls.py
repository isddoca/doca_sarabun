from django.urls import path

from .views import index, DocReceiveListView, DocReceiveCreateView

urlpatterns = [
    path('', index, name='receive'),
    path('receive/', DocReceiveListView.as_view(), name='receive'),
    path('receive/add', DocReceiveCreateView.as_view(), name='receive_create'),
]
