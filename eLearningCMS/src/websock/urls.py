from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'websock'
urlpatterns = [
    path('', views.index)
]
