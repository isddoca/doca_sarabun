from django.urls import include, path
from rest_framework import routers
from .views import DocClassification



# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', DocClassification.as_view(), name='doc_classify'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]