from django.urls import path
from . import views

app_name = 'student'
urlpatterns = [
     path('', views.showStudentHome.as_view(), name="student_home"),
]
