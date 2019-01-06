from django.urls import path
from . import views
from rest_framework.schemas import get_schema_view # new

schema_view = get_schema_view(title='Pastebin API') # new

app_name = 'cdn'
urlpatterns = [
    path('schema/', schema_view), # new
    path('getUploadPaths/<int:count>', views.getUploadPaths),
    path('saveLiveSession/<str:videoKey>/<int:chapterId>', views.saveLiveSession),
    path('getSymetricKey', views.getSymetricKey),
    path('saveClientSession/', views.saveClientSession.as_view(), name='saveClientSession'),
    path('logData/', views.saveLogData.as_view(), name='logData'),
    path('getLogData/<int:providerId>/<str:machineName>', views.getLogData),
    path('clientState/', views.saveClientState.as_view(), name='clientState'),
    path('getClientState/<int:providerId>/<str:machineName>', views.getClientState),
]
