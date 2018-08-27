from django.shortcuts import render
from django.conf import settings
from . import models
import provider
# for interacting jw platform
import jwplatform
import logging
import course
# Rest based modules
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.core import serializers
from .serializers import uploadURLSerializer
from .serializers import CdnSessionSerializer
from rest_framework import status

logger = logging.getLogger("project")

# methods to go here

def createVideoUploadURL(api_key, api_secret):
    jwplatform_client = jwplatform.Client(api_key, api_secret)
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
        logging.error("Encountered an error creating a video\n{}".format(e))

    #import pdb; pdb.set_trace();
    #print("Url: ", upload_url)

    return upload_url

@api_view(['GET'])
def getUploadPaths(request, count, format=None):
    urlList = []
    api_key = 'Add key here'
    api_secret = 'Add secret key here'
    for _ in range(int(count)):
        url = createVideoUploadURL(api_key, api_secret)
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


def getJWClient():
    return jwplatform.Client(settings.JWPLAYER_API_KEY, settings.JWPLAYER_API_SECRET)

def getCourse(courseid):
    return course.models.Course.objects.filter(id=courseid)[0]

def getCdnSession(cdnsessionid):
    return models.CdnSession.objects.filter(id=cdnsessionid)[0]

def getPlaylist(playlistid):
    return models.Playlist.objects.filter(id=playlistid)[0]

def getCdnSessionForSession(sessionid):
    return models.CdnSession.objects.filter(session_id=sessionid)[0]

def getSessionPlaylist(sessionplaylistid):
    return models.SessionPlaylist.objects.filter(id=sessionplsylistid)[0]

def createPlaylist(courseid, **kwargs):
    client = getJWClient()

    try:
        kwargs["title"] = "Playlist for Course " + str(courseid)
        response = client.channels.create(type='manual', **kwargs)

        if response["status"] == "ok":
            playlistObj = models.Playlist(course=getCourse(courseid))
            playlistObj.jwid = response["channel"]["key"]
            playlistObj.save()
            return playlistObj

    except jwplatform.errors.JWPlatformError as e:
        logger.error("Encountered an error creating new channel.\n{}".format(e))
        return None

def insertSessionIntoPlaylist(playlistid, cdnsessionid, **kwargs):
    client = getJWClient()

    try:
        playlistObj = getPlaylist(playlistid)
        cdnsessionObj = getCdnSession(cdnsessionid)

        response = client.channels.videos.create(channel_key=playlistObj.jwid, video_key=cdnsessionObj.jwvideoid, **kwargs)

        if response["status"] == "ok":
            sessionPlaylistObj = models.SessionPlaylist(cdnsession=cdnsessionObj, playlist=playlistObj)
            sessionPlaylistObj.save()
            return sessionPlaylistObj

    except jwplatform.errors.JWPlatformError as e:
        logging.error("Encountered an error inserting {} into channel {}.\n{}".format(cdnsessionObj.jwvideoid, playlistObj.jwid, e))
        return None

