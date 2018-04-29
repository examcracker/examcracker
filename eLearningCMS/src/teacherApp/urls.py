from django.urls import path
from . import views

app_name = 'teacherApp'
urlpatterns = [
     path('', views.showTeacher.as_view(), name="teacherPage"),
]
