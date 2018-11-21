from django.conf.urls import url
from django.urls import path
from . import views

app_name = "schedule"

urlpatterns = [
     path("addShowSchedule", views.addShowSchedule.as_view(), name="add_show_schedule"),
     path("startCapture/<int:chapterid>", views.startCapture.as_view(), name="startCapture"),
     path("stopCapture/<int:chapterid>", views.stopCapture.as_view(), name="stopCapture"),
]
