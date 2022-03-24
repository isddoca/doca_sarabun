from django.conf.urls.static import static
from django.urls import path

from config import settings
from .views import index, DocReceiveListView, doc_receive_add, doc_receive_edit, doc_receive_detail, DocTraceListView, \
    doc_trace_detail, DocTracePendingListView, doc_trace_action

urlpatterns = [
    path('', index, name='receive'),
    path('receive/', DocReceiveListView.as_view(), name='receive'),
    path('receive/<int:id>/', doc_receive_detail, name='receive'),
    path('receive/<int:id>/edit/', doc_receive_edit, name='receive'),
    path('receive/add', doc_receive_add, name='receive'),
    path('trace', DocTraceListView.as_view(), name='trace'),
    path('trace/<int:id>/', doc_trace_detail, name='trace'),
    path('trace/pending/', DocTracePendingListView.as_view(), name='trace_pending'),
    path('trace/pending/<int:id>', doc_trace_action, name='trace_pending'),

]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
