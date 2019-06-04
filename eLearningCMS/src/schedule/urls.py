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
     path("showLiveEvents", views.showLiveEvents.as_view(), name="showLiveEvents"),
     path('playStream/<int:scheduleid>', views.playStream.as_view(), name="playStream"),
     path('on_play', views.on_play.as_view(), name="on_play"),
     path('on_publish', views.on_publish.as_view(), name="on_publish"),
     path('on_publish_done', views.on_publish_done.as_view(), name="on_publish_done"),
     path('deleteSchedule/<int:scheduleid>', views.deleteSchedule.as_view(), name="deleteSchedule"),
]
