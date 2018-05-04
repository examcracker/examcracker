from django.urls import path
from . import views

app_name = 'provider'
urlpatterns = [
     path('', views.showProviderHome.as_view(), name="provider_home"),
     path('uploadVideo', views.uploadVideo.as_view(), name="upload_video"),
     path('createCourse', views.createCourse.as_view(), name="create_course"),
     path('viewCourse', views.viewCourses.as_view(), name="view_courses"),
     path('courseDetail/<int:id>', views.courseDetail.as_view(), name="course_detail"),
     path('viewVideo', views.viewSessions.as_view(), name="view_videos"),
     path('videoDetail/<int:id>', views.sessionDetail.as_view(), name="video_detail"),
]
