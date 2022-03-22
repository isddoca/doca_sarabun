from django.conf.urls.static import static
from django.urls import path

from config import settings
from .views import index, DocReceiveListView, doc_receive_add, doc_receive_edit, doc_receive_detail

urlpatterns = [
    path('', index, name='receive'),
    path('receive/', DocReceiveListView.as_view(), name='receive'),
    path('receive/<int:id>/', doc_receive_detail, name='receive_detail'),
    path('receive/<int:id>/edit/', doc_receive_edit, name='receive_edit'),
    path('receive/add', doc_receive_add, name='receive_add'),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
