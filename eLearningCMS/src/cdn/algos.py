from django.conf import settings
from threading import Thread
import json
import os
import vimeo
import time
import requests
from . import models
import provider
import jwplatform
import logging
import course

logger = logging.getLogger("project")

# methods to go here

def getClient():
    return vimeo.VimeoClient(token=settings.VIMEO_ACCESS_TOKEN, key=settings.VIMEO_CLIENT_ID, secret=settings.VIMEO_CLIENT_SECRET)

def getJWClient():
    return jwplatform.Client(settings.JWPLAYER_API_KEY, settings.JWPLAYER_API_SECRET)

def getCourse(courseid):
    return course.models.Course.objects.filter(id=courseid)[0]

WHITELISTED_DOMAINS = [
    'gyaanhive.com',
    '3Idiots.pythonanywhere.com',
    'localhost',
    '127.0.0.1'
    ]

def threadedPushVideo(sessionObj):
    vimeoclient = getClient()
    fullPath = os.path.join(settings.MEDIA_ROOT, sessionObj.video.path)
    uri = vimeoclient.upload(fullPath)

    vimeoclient.patch(uri, data = {
                            'name' : 'Session ' + str(sessionObj.id),
                            'description' : 'Session with Id ' + str(sessionObj.id),
                            'privacy' : {
                                'view' : 'disable',
                                'download' : "false",
                                'add' : "false",
                                'comments' : 'nobody',
                                'embed' : 'whitelist',
                            }
                        })

    vimeo_id = str.split(uri, "/videos/")[1]

    url = 'https://api.vimeo.com/videos/' + vimeo_id + '/privacy/domains/'
    for d in WHITELISTED_DOMAINS:
        finalurl = url + d
        response = requests.put(url=finalurl, headers={"Authorization":"bearer " + settings.VIMEO_ACCESS_TOKEN})

    cdnSessionObj = models.cdnSession()
    cdnSessionObj.session = sessionObj
    cdnSessionObj.vimeo = vimeo_id
    cdnSessionObj.save()

    geturl = 'https://api.vimeo.com/videos/' + vimeo_id
    ready = False

    while not ready:
        time.sleep(120)
        response = requests.get(url=geturl, headers={"Authorization":"bearer " + settings.VIMEO_ACCESS_TOKEN})
        if response.status_code == 200:
            videodata = response.json()

            duration = int(videodata['duration'])
            if duration > 0:
                ready = True

            sessionObj = provider.models.Session.objects.filter(id=sessionObj.id)[0]
            sessionObj.duration = duration
            sessionObj.save()
            cdnSessionObj.ready = True
            cdnSessionObj.html = videodata['embed']['html']
            cdnSessionObj.save()

    os.remove(fullPath)

def pushVideo(sessionObj):
    t = Thread(target=threadedPushVideo, args=(sessionObj,))
    t.start()

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
