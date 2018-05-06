from django.urls import path
from . import views

app_name = 'student'
urlpatterns = [
     path('', views.showStudentHome.as_view(), name="student_home"),
     path('joinCourse', views.joinCourses.as_view(), name="join_courses"),
     path('myCourse', views.myCourses.as_view(), name="my_courses"),
     path('courseDetails/<int:id>', views.courseDetails.as_view(), name="course_details"),
     path('videoDetails/<int:id>', views.sessionDetails.as_view(), name="video_details"),
]
