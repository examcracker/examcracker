from django.urls import path
from . import views

app_name = 'provider'
urlpatterns = [
     path('', views.showTeacher.as_view(), name="provider_home"),
]
