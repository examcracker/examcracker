from django.shortcuts import render
from django.conf import settings
from . import models
import provider
import jwplatform
import logging
import course

logger = logging.getLogger("project")

# methods to go here

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

