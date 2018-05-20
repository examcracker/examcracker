from django.urls import path
from . import views

app_name = 'course'
urlpatterns = [
     path('coursePage', views.courseDetails.as_view(), name="coursePage"),
]
