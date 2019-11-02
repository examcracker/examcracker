from django.urls import path
from . import views
from rest_framework.schemas import get_schema_view # new

schema_view = get_schema_view(title='Pastebin API') # new

app_name = 'course'
urlpatterns = [
     path('coursePage/<int:id>', views.courseDetails.as_view(), name="coursePage"),
     path('addReview/<int:id>', views.addReview.as_view(), name="addReview"),
     path('playSession/<int:chapterid>/<int:sessionid>', views.playSession.as_view(), name="playSession"),
     path('playSessionEnc/<int:chapterid>/<int:sessionid>', views.playSessionEnc.as_view(), name="playSessionEnc"),
     path('updateDurationPlayed/<int:enrolledcourseid>/<int:duration>/<int:live>', views.updateDuration),
     path('updateDurationPlayedProvider/<int:courseid>/<int:duration>', views.updateDurationProvider),
]
