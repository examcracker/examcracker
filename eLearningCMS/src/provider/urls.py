from django.urls import path
from . import views

app_name = 'provider'
urlpatterns = [
     path('', views.showProviderHome.as_view(), name="provider_home"),
     path('uploadVideo', views.uploadVideo.as_view(), name="upload_video"),
     path('createCourse', views.createCourse.as_view(), name="create_course"),
     path('editCourse/<int:id>', views.editCourse.as_view(), name="edit_course"),
     path('profile', views.ProviderProfile.as_view(), name="my_profile"),
     path('viewCourse', views.viewCourses.as_view(), name="view_courses"),
     path('viewVideo', views.viewSessions.as_view(), name="view_videos"),
     path('publishCourse', views.publishCourse.as_view(), name="publish_course"),
     path('createFromCourses', views.createFromCourses.as_view(), name="create_from_courses"),
     path('verifyEmail/<slug:slug>', views.VerifyEmail.as_view(), name="verify_email"),
     path('myStudents', views.myStudents.as_view(), name="my_students"),
     path('liveCapture', views.liveCapture.as_view(), name="live_capture"),
     path('addStudents/<slug:slug>', views.addStudents.as_view(), name="add_students"),
     path('getProviderProfile/<str:email>/<str:encpassword>', views.ProviderCourseDetails.as_view(), name="provider_profile"),
     path('deleteCourse/<int:id>', views.deleteCourse.as_view(), name="delete_course"),
     path('export_studentdata/<int:studentid>', views.export_users_csv, name='export_studentdata'),
     path('fix_expiry', views.fix_expiry, name='fix_expiry')
]
