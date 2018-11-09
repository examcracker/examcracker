from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'schedule'

urlpatterns = [
     path('addShowSchedule', views.addShowSchedule.as_view(), name="add_show_schedule")
]
