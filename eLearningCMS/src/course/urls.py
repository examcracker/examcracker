from django.urls import path
from . import views

app_name = 'course'
urlpatterns = [
     path('coursePage/<int:id>', views.courseDetails.as_view(), name="coursePage"),
     path('playSession/<int:courseid>/<int:sessionid>', views.playSession.as_view(), name="playSession"),
]
