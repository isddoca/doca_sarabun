from django.urls import path

from .views import index, send_index

urlpatterns = [
    path('', index),
    path('send/', send_index),
]
