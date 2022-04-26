from django.conf.urls.static import static
from django.urls import path

from config import settings
from .views import linenotify
from .views import order
from .views import base
from .views import receive
from .views import send
from .views import trace


urlpatterns = [
    path('', receive.DocReceiveListView.as_view(), name='receive'),
    path('fulfillment', base.fulfillment, name='fulfillment'),
    path('accounts/edit', base.user_info_edit, name='account'),

    path('linenotify/register', linenotify.line_notify_register, name='linenotify'),
    path('linenotify/callback', linenotify.line_notify_callback, name='linenotify'),
    path('linenotify/revoke', linenotify.line_notify_revoke, name='linenotify'),

    path('receive/', receive.DocReceiveListView.as_view(), name='receive'),
    path('receive/<int:id>/', receive.doc_receive_detail, name='receive'),
    path('receive/<int:id>/edit/', receive.doc_receive_edit, name='receive'),
    path('receive/<int:id>/delete/', receive.doc_receive_delete, name='receive_delete'),
    path('receive/add', receive.doc_receive_add, name='receive'),
    path('receive/credential', receive.DocReceiveCredentialListView.as_view(), name='receive_credential'),
    path('receive/credential/<int:id>/', receive.doc_receive_detail, name='receive_credential'),
    path('receive/credential/add', receive.doc_receive_add, name='receive_credential'),
    path('receive/credential/<int:id>/edit/', receive.doc_receive_edit, name='receive_credential'),

    path('send/', send.DocSendListView.as_view(), name='send'),
    path('send/<int:id>/', send.doc_send_detail, name='send'),
    path('send/<int:id>/edit/', send.doc_send_edit, name='send'),
    path('send/<int:id>/delete/', send.doc_send_delete, name='send_delete'),
    path('send/add', send.doc_send_add, name='send'),
    path('send/credential', send.DocSendCredentialListView.as_view(), name='send_credential'),
    path('send/credential/add', send.doc_send_add, name='send_credential'),
    path('send/credential/<int:id>/', send.doc_send_detail, name='send_credential'),
    path('send/credential/<int:id>/edit/', send.doc_send_edit, name='send_credential'),
    path('send/out', send.DocSendOutListView.as_view(), name='send_out'),
    path('send/out/<int:id>/', send.doc_send_detail, name='send_out'),
    path('send/out/<int:id>/edit/', send.doc_send_edit, name='send_out'),
    path('send/out/add', send.doc_send_add, name='send_out'),
    path('send/out/credential', send.DocSendCredentialOutListView.as_view(), name='send_credential_out'),
    path('send/out/credential/add', send.doc_send_add, name='send_credential_out'),
    path('send/out/credential/<int:id>/', send.doc_send_detail, name='send_credential_out'),
    path('send/out/credential/<int:id>/edit/', send.doc_send_edit, name='send_credential_out'),

    path('trace', trace.DocTraceListView.as_view(), name='trace'),
    path('trace/<int:id>/', trace.doc_trace_detail, name='trace'),
    path('trace/pending/', trace.DocTracePendingListView.as_view(), name='trace_pending'),
    path('trace/pending/<int:id>', trace.doc_trace_action, name='trace_pending'),

    path('order/', order.DocOrderListView.as_view(), name='order'),
    path('order/<int:id>/', order.doc_order_detail, name='order'),
    path('order/<int:id>/edit/', order.doc_order_edit, name='order'),
    path('order/<int:id>/delete/', order.doc_order_delete, name='order_delete'),
    path('order/add', order.doc_order_add, name='order'),
    path('order/specific', order.DocOrderSpecificListView.as_view(), name='order_specific'),
    path('order/specific/<int:id>/', order.doc_order_detail, name='order_specific'),
    path('order/specific/<int:id>/edit/', order.doc_order_edit, name='order_specific'),
    path('order/specific/add', order.doc_order_add, name='order_specific'),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
