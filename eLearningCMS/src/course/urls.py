from django.urls import path
from . import views

app_name = 'course'
urlpatterns = [
     path('coursePage/<int:id>', views.courseDetails.as_view(), name="coursePage"),
     path('addReview/<int:id>', views.addReview.as_view(), name="addReview"),
     path('playSession/<int:chapterid>/<int:sessionid>', views.playSession.as_view(), name="playSession"),
]
