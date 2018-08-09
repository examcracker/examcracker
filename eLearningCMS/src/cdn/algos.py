from django.conf import settings
from threading import Thread
import json
import os
import vimeo
import requests
from . import models

# methods to go here

def getClient():
    return vimeo.VimeoClient(token=settings.VIMEO_ACCESS_TOKEN, key=settings.VIMEO_CLIENT_ID, secret=settings.VIMEO_CLIENT_SECRET)

WHITELISTED_DOMAINS = [
    'gyaanhive.com',
    '3Idiots.pythonanywhere.com',
    'localhost'
    ]

def threadedPushVideo(sessionObj):
    vimeoclient = getClient()
    uri = vimeoclient.upload(os.path.join(settings.MEDIA_ROOT, sessionObj.video.path))

    vimeoclient.patch(uri, data = {
                            'name' : 'Session ' + str(sessionObj.id),
                            'description' : 'Session with Id ' + str(sessionObj.id),
                            'privacy' : {
                                'view' : 'nobody',
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

def pushVideo(sessionObj):
    t = Thread(target=threadedPushVideo, args=(sessionObj,))
    t.start()
