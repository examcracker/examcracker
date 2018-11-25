from django.shortcuts import render
from django.conf import settings
from django.views import generic
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
from examcracker import thread
# crypto
from Crypto.Random import get_random_bytes
import base64

logger = logging.getLogger("project")

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
    path = 'players/' + jwid + '-zRzB2xDB.html'
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
    sessionObj.name = str(providerObj.id) + str(datetime.datetime.now().isoformat())
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
    return Response(saveSession(videoKey, chapterId))

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
        return super().get(request, *args, **kwargs)
