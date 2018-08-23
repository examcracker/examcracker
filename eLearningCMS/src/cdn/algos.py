from django.conf import settings
from threading import Thread
import json
import os
import time
import requests
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
