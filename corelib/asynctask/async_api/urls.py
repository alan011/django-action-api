from django.urls import path
from .api import APIIngress

urlpatterns = [
    path('api/v1', APIIngress.as_view(), name="asynctask_api"),
]
