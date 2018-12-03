from django.conf.urls import url
from django.urls import path
from . import views

app_name = "schedule"

urlpatterns = [
     path("addShowSchedule", views.addShowSchedule.as_view(), name="add_show_schedule"),
     path("startCapture/<int:scheduleid>", views.startCapture.as_view(), name="startCapture"),
     path("stopCapture/<int:scheduleid>", views.stopCapture.as_view(), name="stopCapture"),
     path("systemName", views.addSystem.as_view(), name="systemName"),
     path("captureState/<int:scheduleid>", views.captureState.as_view(), name="captureState"),
]
