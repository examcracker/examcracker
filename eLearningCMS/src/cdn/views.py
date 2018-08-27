from django.shortcuts import render
from django.conf import settings
from . import models
import provider
# for interacting jw platform
import jwplatform
import course
# Rest based modules
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.core import serializers
from .serializers import uploadURLSerializer
from .serializers import CdnSessionSerializer
from rest_framework import status

import logging

import hashlib
import time

logger = logging.getLogger("project")

# methods to go here
IST_UTC = 3600*5 + 1800

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
    expiry = str(int(time.time()) + IST_UTC + 3600*6)
    digest = hashlib.md5((path + ':' + expiry + ':' + settings.JWPLAYER_API_SECRET).encode()).hexdigest()
    url = 'https://content.jwplatform.com/' + path + '?exp=' + expiry + '&sig=' + digest
    return url

def getVideoDuration(jwid):
    jwplatform_client = getJWClient()
    try:
        response = jwplatform_client.videos.show(jwid)
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

    #import pdb; pdb.set_trace();
    #print("Url: ", upload_url)

    return upload_url

@api_view(['GET'])
def getUploadPaths(request, count, format=None):
    urlList = []
    for _ in range(int(count)):
        url = createVideoUploadURL()
        urlList.append({"url": url})

    serializer = uploadURLSerializer(urlList, many=True)
    return Response(serializer.data)

#@api_view(['POST'])
#def createSession(request, videoKey, sessionId):
#    session = models.CdnSession()
#    session.jwvideoid = videoKey
#    session.ready = False
#    session.session = sessionId
#    session.save()
#    return Response("Success", status=status.HTTP_201_CREATED)

    # serializer = CdnSessionSerializer(data=request.data)
    # if serializer.is_valid():
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
    # else:
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


