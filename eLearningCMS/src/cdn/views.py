from django.shortcuts import render
from django.conf import settings
from . import models
import jwplatform
import course
import hashlib
import time

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
