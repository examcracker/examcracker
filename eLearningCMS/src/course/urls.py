from django.urls import path
from . import views
from rest_framework.schemas import get_schema_view # new

schema_view = get_schema_view(title='Pastebin API') # new

app_name = 'course'
urlpatterns = [
     path('coursePage/<int:id>', views.courseDetails.as_view(), name="coursePage"),
     path('addReview/<int:id>', views.addReview.as_view(), name="addReview"),
     path('playSession/<int:chapterid>/<int:sessionid>', views.playSession.as_view(), name="playSession"),
     path('updateDurationPlayed/<int:enrolledcourseid>/<int:duration>', views.updateDuration),
     path('authPlay', views.authPlay.as_view(), name="authPlay"),
     path('authPublish', views.authPublish.as_view(), name="authPublish"),
     path('on_publish_done', views.on_publish_done.as_view(), name="on_publish_done"),
]
