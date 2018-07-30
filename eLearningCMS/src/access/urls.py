from django.urls import path
from . import views

app_name = 'access'
urlpatterns = [
     path('allow/<int:userid>/<str:deviceinfo>', views.allowDevice.as_view(), name="allow"),
]
