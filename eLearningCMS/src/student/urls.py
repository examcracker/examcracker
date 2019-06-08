from django.urls import path
from . import views

app_name = 'student'
urlpatterns = [
     path('', views.showStudentHome.as_view(), name="student_home"),
     path('myCourse', views.myCourses.as_view(), name="my_courses"),
     path('profile', views.StudentProfile.as_view(), name="my_profile"),
     path('recommendation', views.showRecommendedCourses.as_view(), name="recommended_courses"),
     path('progress', views.showProgress.as_view(), name="progress"),
     path('courseDetails/<int:id>', views.courseDetails.as_view(), name="course_details"),
     path('videoDetails/<int:id>', views.sessionDetails.as_view(), name="video_details"),
     path('searchCourse', views.searchCourses.as_view(), name="search_courses"),
     path('verifyEmail/<slug:slug>', views.VerifyEmail.as_view(), name='verify_email'),
     path('view_hours/', views.view_hours.as_view(), name='view_hours')
]
