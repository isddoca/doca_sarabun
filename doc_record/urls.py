from django.urls import path

from .views import index, DocReceiveListView

urlpatterns = [
    path('', index, name='receive'),
    path('receive/', DocReceiveListView.as_view(), name='receive'),
]
