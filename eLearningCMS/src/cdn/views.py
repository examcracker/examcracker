from django.shortcuts import render
from django.conf import settings
from django.views import generic
from django.contrib.auth import get_user_model
from django.conf import settings
from . import models
import provider
# for interacting jw platform
import jwplatform
import course
# Rest based modules
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.http import JsonResponse
from django.core import serializers
from .serializers import uploadURLSerializer
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
import logging
import hashlib
import time
import datetime
import json
import schedule
from examcracker import thread
# crypto
from Crypto.Random import get_random_bytes
import base64
from profiles.signals import sendMail
from course.algos import strToIntList
# pusher
import pusher
import pysher

logger = logging.getLogger("project")

User = get_user_model()

command_upload_logs = 2
command_get_recent_capture_file_details = 3
command_check_client_active = 5

# methods to go here
EXPIRY_BANDWIDTH = 3600*5

def getJWClient():
    return jwplatform.Client(settings.JWPLAYER_API_KEY, settings.JWPLAYER_API_SECRET)

def getCourse(courseid):
    return course.models.Course.objects.filter(id=courseid)[0]

def getCdnSession(cdnsessionid):
    return models.CdnSession.objects.filter(id=cdnsessionid)[0]

def getCdnSessionForSession(sessionid):
    return models.CdnSession.objects.filter(session_id=sessionid)[0]

def getSignedUrl(jwid):
    #path = 'players/' + jwid + '-zRzB2xDB.html'
    path = 'manifests/' + jwid + '.m3u8'
    expiry = str(int(time.time()) + EXPIRY_BANDWIDTH)
    digest = hashlib.md5((path + ':' + expiry + ':' + settings.JWPLAYER_API_SECRET).encode()).hexdigest()
    url = 'https://content.jwplatform.com/' + path + '?exp=' + expiry + '&sig=' + digest

    return url


def getVideoDuration(jwid):
    jwplatform_client = getJWClient()
    try:
        response = jwplatform_client.videos.show(video_key=jwid)
        duration = float(response["video"]["duration"])
        return duration

    except jwplatform.errors.JWPlatformError as e:
        logger.error("Encountered an error querying for videos duration.\n{}".format(e))
        return None

def createVideoUploadURL():
    jwplatform_client = getJWClient()
    upload_url = ''
    try:
        response = jwplatform_client.videos.create()

        upload_url = '{}://{}{}?api_format=xml&key={}&token={}'.format(
            response['link']['protocol'],
            response['link']['address'],
            response['link']['path'],
            response['link']['query']['key'],
            response['link']['query']['token']
        )

    except jwplatform.errors.JWPlatformError as e:
        logger.error("Encountered an error creating a video\n{}".format(e))

    return upload_url

def getProviderFromChapterId(chapterid):
    chapterObj = course.models.CourseChapter.objects.filter(id=chapterid)[0]
    courseObj = course.models.Course.objects.filter(id=chapterObj.course_id)[0]
    providerObj = provider.models.Provider.objects.filter(id=courseObj.provider_id)[0]
    return providerObj

# methods to be called from provider client
def saveSession(videoKey, chapterId, publish=False):
    chapterObj = course.models.CourseChapter.objects.filter(id=chapterId)[0]
    providerObj = getProviderFromChapterId(chapterId)
    sessionObj = provider.models.Session()
    # session file Naming convention : chapter_date_sessionNumber
    dateTimeStr = datetime.datetime.now().strftime("%B %d, %Y")
    sessionids = strToIntList(chapterObj.sessions)
    sessionObj.name = chapterObj.name + '_' + dateTimeStr + '_' + str(len(sessionids)+1)
    
    sessionObj.videoKey = videoKey
    sessionObj.provider_id = providerObj.id
    sessionObj.tags = chapterObj.subject
    sessionObj.save()

    publishstatus = "0"
    if publish:
        publishstatus = "1"

    if len(chapterObj.sessions) > 0:
        chapterObj.sessions = chapterObj.sessions + "," + str(sessionObj.id)
    else:
        chapterObj.sessions = str(sessionObj.id)
    if len(chapterObj.published) > 0:
        chapterObj.published = chapterObj.published + "," + publishstatus
    else:
        chapterObj.published = publishstatus
    chapterObj.save()

    # create thread to compute duration
    callbackObj = provider.views.SessionDurationFetch(sessionObj)
    t = thread.AppThread(callbackObj, True, 30)
    t.start()

    # send mail to provider that new session has been added
    userObj = User.objects.filter(id=providerObj.user_id)[0]
    subject = "New session available for chapter " + chapterObj.name
    emailBody = '\
    Dear ' + userObj.name + ',\
        New session has been added for chapter ' + chapterObj.name + '.\
        If you have not enabled auto publish your schedule, kindly go to course page and click\
        on publish to make it visible to your students. For any issues , kindly contact us.\
    Thanks\
    GyaanHive Team\
    '

    #sendMail(userObj.email, subject,emailBody)

def saveLiveSessionInt(videoKey, chapterId):
    saveSession(videoKey, chapterId)
    return {"result":True}

@api_view(['GET'])
@authentication_classes((SessionAuthentication, ))
@permission_classes((IsAuthenticated, ))
def getUploadPaths(request, count, format=None):
    urlList = []
    for _ in range(int(count)):
        url = createVideoUploadURL()
        urlList.append({"url": url})

    serializer = uploadURLSerializer(urlList, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@authentication_classes((SessionAuthentication, ))
@permission_classes((IsAuthenticated, ))
def saveLiveSession(request, videoKey, chapterId):
    return Response(saveLiveSessionInt(videoKey, chapterId))

@api_view(['GET'])
@authentication_classes((SessionAuthentication, ))
@permission_classes((IsAuthenticated, ))
def getSymetricKey(request):
    key = get_random_bytes(16)
    iv = get_random_bytes(16)
    return Response({"key":base64.b64encode(key).decode(), "iv":base64.b64encode(iv).decode()})

class saveClientSession(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        jsonObj = json.loads(request.body.decode())
        saveSession(jsonObj["videokey"], jsonObj["chapterid"], bool(jsonObj["publish"]))
        return schedule.views.HttpResponseNoContent()

@api_view(['GET'])
@authentication_classes((SessionAuthentication, ))
@permission_classes((IsAuthenticated, ))
def getLogData(request, providerId, machineName):
    if not request.user.is_superuser:
        return Response({"status":False})

    providerObj = provider.models.Provider.objects.filter(id=providerId)[0]
    reqDict = {}
    reqDict["command"] = command_upload_logs
    reqDict["machine"] = machineName
    pusherObj = pusher.Pusher(app_id=settings.PUSHER_APP_ID, key=settings.PUSHER_KEY, secret=settings.PUSHER_SECRET, cluster=settings.PUSHER_CLUSTER, ssl=True)
    pusherObj.trigger(str(providerObj.id), str(providerObj.id), reqDict)
    return Response({"status":True})

class saveLogData(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        jsonObj = json.loads(request.body.decode())
        encryptedId = jsonObj["id"]
        contents = jsonObj["logs"]
        logObj = models.Logs.objects.filter(providerencryptedid=encryptedId)
        if len(logObj) == 0:
            logObj = models.Logs()
        else:
            logObj = logObj[0]
        logObj.providerencryptedid = encryptedId
        logObj.contents = contents
        logObj.save()
        return schedule.views.HttpResponseNoContent()

@api_view(['GET'])
@authentication_classes((SessionAuthentication, ))
@permission_classes((IsAuthenticated, ))
def getClientState(request, providerId, machineName):
    if not request.user.is_superuser:
        return Response({"status":False})

    providerObj = provider.models.Provider.objects.filter(id=providerId)[0]
    reqDict = {}
    reqDict["command"] = command_check_client_active
    reqDict["machine"] = machineName
    pusherObj = pusher.Pusher(app_id=settings.PUSHER_APP_ID, key=settings.PUSHER_KEY, secret=settings.PUSHER_SECRET, cluster=settings.PUSHER_CLUSTER, ssl=True)
    pusherObj.trigger(str(providerObj.id), str(providerObj.id), reqDict)
    return Response({"status":True})

class saveClientState(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        jsonObj = json.loads(request.body.decode())
        encryptedId = jsonObj["id"]
        state = jsonObj["result"]
        stateObj = models.ClientState.objects.filter(providerencryptedid=encryptedId)
        if len(stateObj) == 0:
            stateObj = models.ClientState()
        else:
            stateObj = stateObj[0]
        stateObj.providerencryptedid = encryptedId
        stateObj.state = state
        stateObj.save()
        return schedule.views.HttpResponseNoContent()

@api_view(['GET'])
@authentication_classes((SessionAuthentication, ))
@permission_classes((IsAuthenticated, ))
def getFileDetails(request, providerId, machineName):
    if not request.user.is_superuser:
        return Response({"status":False})

    providerObj = provider.models.Provider.objects.filter(id=providerId)[0]
    reqDict = {}
    reqDict["command"] = command_get_recent_capture_file_details
    reqDict["machine"] = machineName
    pusherObj = pusher.Pusher(app_id=settings.PUSHER_APP_ID, key=settings.PUSHER_KEY, secret=settings.PUSHER_SECRET, cluster=settings.PUSHER_CLUSTER, ssl=True)
    pusherObj.trigger(str(providerObj.id), str(providerObj.id), reqDict)
    return Response({"status":True})

class saveFileDetails(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        jsonObj = json.loads(request.body.decode())
        encryptedId = jsonObj["id"]
        details = request.body.decode()
        fileDetObj = models.FileDetails.objects.filter(providerencryptedid=encryptedId)
        if len(fileDetObj) == 0:
            fileDetObj = models.FileDetails()
        else:
            fileDetObj = fileDetObj[0]
        fileDetObj.providerencryptedid = encryptedId
        fileDetObj.state = state
        fileDetObj.save()
        return schedule.views.HttpResponseNoContent()
