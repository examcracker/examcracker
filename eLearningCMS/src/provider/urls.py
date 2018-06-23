from django.urls import path
from . import views

app_name = 'provider'
urlpatterns = [
     path('', views.showProviderHome.as_view(), name="provider_home"),
     path('uploadVideo', views.uploadVideo.as_view(), name="upload_video"),
     path('createCourse', views.createCourse.as_view(), name="create_course"),
     path('profile', views.showStudentProfile.as_view(), name="my_profile"),
     path('viewCourse', views.viewCourses.as_view(), name="view_courses"),
     path('viewVideo', views.viewSessions.as_view(), name="view_videos"),
     path('publishCourse', views.publishCourse.as_view(), name="publish_course"),
     path('createFromCourses', views.createFromCourses.as_view(), name="create_from_courses"),
]
