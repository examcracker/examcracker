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
from datetime import datetime
import calendar
import logging
import hashlib
import time
import datetime
import json
import schedule
import student
from examcracker import thread
# crypto
from Crypto.Random import get_random_bytes
import base64
from profiles.signals import sendMail
from course.algos import strToIntList
# pusher
import pusher
import pysher
import os
# http
import requests

logger = logging.getLogger("project")

User = get_user_model()

command_upload_logs = 2
command_get_recent_capture_file_details = 3
command_upload_file = 4
command_check_client_active = 5

# methods to go here
EXPIRY_BANDWIDTH = 30

def getClearKey():
    DRM_keyID = os.urandom(16).hex()
    DRM_key = os.urandom(16).hex()
    return {'KeyID': DRM_keyID, 'Key': DRM_key}

def getJWClient():
    return jwplatform.Client(settings.JWPLAYER_API_KEY, settings.JWPLAYER_API_SECRET)

def getDevAccJWClient():
    return jwplatform.Client(settings.JWPLAYER_DEV_ACC_API_KEY, settings.JWPLAYER_DEV_ACC_API_SECRET)

def getCourse(courseid):
    return course.models.Course.objects.filter(id=courseid)[0]

def getCdnSession(cdnsessionid):
    return models.CdnSession.objects.filter(id=cdnsessionid)[0]

def getCdnSessionForSession(sessionid):
    return models.CdnSession.objects.filter(session_id=sessionid)[0]

def getEncryptedVideoUrl(jwid):
    url = 'https://gyaanhive.sgp1.cdn.digitaloceanspaces.com/'+ jwid + '/' + jwid + '.mpd'
    return url
    jwc = getDevAccJWClient()

    try:
        conversions = jwc.videos.conversions.list(video_key=jwid)
        if conversions['status'] != 'ok':
            return None

        passthrough = {}
        for c in conversions["conversions"]:
            if c['template']['format']['key'] == 'passthrough':
                passthrough = c
                break

        url = 'https://content.jwplatform.com/videos/' + jwid + '-' + passthrough['template']['key'] + '.mp4'
        return url

    except jwplatform.errors.JWPlatformError as e:
        logger.error("Encountered an error querying for videos passthrough url.\n{}".format(e))
        return None

def getSignedUrl(jwid):
    path = 'manifests/' + jwid + '.m3u8'
    expiry = str(int(time.time()) + EXPIRY_BANDWIDTH)
    digest = hashlib.md5((path + ':' + expiry + ':' + settings.JWPLAYER_API_SECRET).encode()).hexdigest()
    url = 'https://content.jwplatform.com/' + path + '?exp=' + expiry + '&sig=' + digest
    retdict = {}
    retdict['expiry'] = expiry
    retdict['digest'] = digest
    return retdict

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
def saveSession(videoKey, chapterId, publish=False, encrypted=False, drmkeyid='', drmkey='', duration=0, sessionName='', dobucketname='', bunnyCDNStorageName=''):
    chapterObj = course.models.CourseChapter.objects.filter(id=chapterId)[0]
    providerObj = getProviderFromChapterId(chapterId)
    sessionObj = provider.models.Session()

    # session file Naming convention : chapter_date_sessionNumber
    dateTimeStr = datetime.datetime.now().strftime("%B %d, %Y")
    sessionids = strToIntList(chapterObj.sessions)
    if sessionName == '':
        sessionObj.name = chapterObj.name + '_' + dateTimeStr + '_' + str(len(sessionids)+1)
    else:
        sessionObj.name = sessionName
    sessionObj.videoKey = videoKey
    sessionObj.provider_id = providerObj.id
    sessionObj.tags = chapterObj.subject
    sessionObj.encrypted = encrypted
    sessionObj.duration = duration
    if duration > 0:
        sessionObj.ready = True
    # for testing , give preference to bunny CDN
    #if dobucketname != '':
    #    sessionObj.bucketname = dobucketname
    if bunnyCDNStorageName != '':
        sessionObj.bucketname = bunnyCDNStorageName
    sessionObj.save()

    if encrypted:
        drmsessionObj = provider.models.DrmSession()
        drmsessionObj.session_id = sessionObj.id
        drmsessionObj.keyid = drmkeyid
        drmsessionObj.key = drmkey
        drmsessionObj.save()

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

    # send mail to provider that new session has been added
    userObj = User.objects.filter(id=providerObj.user_id)[0]
    subject = "Session available for " + chapterObj.name

    emailBody = '<p>Dear <span style="color: #ff0000;"><strong>' + userObj.name + '\n\
</strong></span>,<br />New session has been added for chapter <em><strong>' + chapterObj.name + '</strong></em>.<br />\n\
If you have not enabled <em>auto publish</em> for your schedule, kindly go to your <a href="https://www.gyaanhive.com/course/coursePage/' + str(chapterObj.course_id) + '">Course</a> and click on <em>Publish</em> to make it available to your students.<br />\n\
For any issues, kindly contact us.<br />\n\
Thanks</p>\
<p>GyaanHive Team</p>'

    sendMail(userObj.email, subject, emailBody)

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
        sessionName = ''
        dobucketname = ''
        bunnyCDNStorageName = ''
        if "sessionName" in jsonObj:
            sessionName = jsonObj["sessionName"]
        if 'bucketname' in jsonObj:
            dobucketname = jsonObj["bucketname"]
        if 'bunnyCDNStorageName' in jsonObj:
            bunnyCDNStorageName = jsonObj["bunnyCDNStorageName"]
        if 'primary' in jsonObj:
            primary = jsonObj["primary"]
            if primary == schedule.views.DO:
                bunnyCDNStorageName = ''
        saveSession(jsonObj["videokey"], jsonObj["chapterid"], bool(jsonObj["publish"]), bool(jsonObj["encrypted"]),
                    jsonObj["drmkeyid"], jsonObj["drmkey"], jsonObj["duration"],sessionName,dobucketname,bunnyCDNStorageName)
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
        fileDetObj.details = details
        fileDetObj.save()
        return schedule.views.HttpResponseNoContent()

def sendUploadFileReq(scheduleId, machineName, fileName):
    scheduleObj = schedule.models.Schedule.objects.filter(id=scheduleId)[0]
    providerObj = provider.models.Provider.objects.filter(id=scheduleObj.provider_id)[0]

    reqDict = {}
    reqDict["filePath"] = fileName
    reqDict["command"] = command_upload_file
    reqDict["id"] = providerObj.encryptedid
    reqDict["machine"] = machineName
    reqDict["publish"] = scheduleObj.autopublish
    reqDict["chapterid"] = scheduleObj.chapter_id

    pusherObj = pusher.Pusher(app_id=settings.PUSHER_APP_ID, key=settings.PUSHER_KEY, secret=settings.PUSHER_SECRET, cluster=settings.PUSHER_CLUSTER, ssl=True)
    pusherObj.trigger(str(providerObj.id), str(providerObj.id), reqDict)

@api_view(['GET'])
@authentication_classes((SessionAuthentication, ))
@permission_classes((IsAuthenticated, ))
def postUploadFile(request, scheduleId, machineName, fileName):
    if not request.user.is_superuser:
        return Response({"status":False})

    sendUploadFileReq(scheduleId, machineName, fileName)
    return Response({"status":True})

class saveFileUpload(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        jsonObj = json.loads(request.body.decode())
        encryptedId = jsonObj["id"]
        details = request.body.decode()
        fileUploadObj = models.FileUpload.objects.filter(providerencryptedid=encryptedId)
        if len(fileUploadObj) == 0:
            fileUploadObj = models.FileUpload()
        else:
            fileUploadObj = fileUploadObj[0]

        fileUploadObj.providerencryptedid = encryptedId
        fileUploadObj.status = details
        fileUploadObj.save()
        return schedule.views.HttpResponseNoContent()

def getProviderStudentsInt(start, end, courseid):
    courseObj = course.models.Course.objects.filter(id=courseid)[0]
    studentsObj = course.models.EnrolledCourse.objects.filter(course_id=courseObj.id)

    studentList = []
    moreStudents = False

    if start < 0:
        start = 0
    if start >= len(studentsObj):
        start = len(studentsObj) - 1
    if end <= 0 or end > len(studentsObj):
        end = len(studentsObj)
    if start + end > len(studentsObj):
        end = len(studentsObj) - start

    if start + end < len(studentsObj):
        moreStudents = True

    i = 0

    while i < end:
        studentItem = studentsObj[start]
        studentInfo = {}
        studentDetails = student.models.Student.objects.filter(id=studentItem.student_id)[0]
        studentInfo['id'] = studentDetails.id
        studentInfo['name'] = course.algos.getUserNameAndPic(studentDetails.user_id)['name']

        datetoshow = str(studentItem.enrolled.day) + " " + calendar.month_name[studentItem.enrolled.month][:3] + " " + str(studentItem.enrolled.year) + ", "
        expiry = str(studentItem.expiry.day) + " " + calendar.month_name[studentItem.expiry.month][:3] + " " + str(studentItem.expiry.year) + ", "
        '''
        meridian = "A.M"
        hours = studentItem.enrolled.hour
        minutes = studentItem.enrolled.minute
        if hours > 12:
            hours = hours - 12
            meridian = "P.M"
        strh = str(hours)
        if hours < 10:
            strh = "0" + strh
        strm = str(minutes)
        if minutes < 10:
            strm = "0" + strm
        datetoshow = datetoshow + strh + ":" + strm + " " + meridian
        '''
        studentInfo['enrolled_date'] = datetoshow
        studentInfo['course_expiry'] = expiry
        studentInfo['remarks'] = studentItem.remarks
        studentInfo['viewhours'] = studentItem.viewhours
        studentInfo['completedminutes'] = int(studentItem.completedminutes+0.5)
        studentList.append(studentInfo)
        start = start + 1
        i = i + 1

    return (moreStudents, studentList)

@api_view(['GET'])
@authentication_classes((SessionAuthentication, ))
@permission_classes((IsAuthenticated, ))
def getProviderStudents(request, start, end, courseid):
    if not request.user.is_staff:
        return Response({"status":False})
    moreStudents, studentList = getProviderStudentsInt(start, end, courseid)
    return Response({"status":True, "students":studentList, "more":moreStudents})

class ProviderStats:
    storage = None
    bandwidth = None
    files = None

def getBunnyStats(providerid):
    p = ProviderStats()

    storagename = 'gyaanhive' + str(providerid)
    pullzoneUrl = 'https://bunnycdn.com/api/pullzone/'
    headers = {'content-type': 'application/json', 'Accept': 'application/json', 'AccessKey': settings.BUNNY_API_KEY}

    try:
        r = requests.get(pullzoneUrl, headers=headers)
    except requests.ConnectionError:
        return (None, None, None)

    data = r.json()
    storageid = None
    pullzoneid = None

    for d in data:
        if d["Name"] == storagename:
            storageid = int(d["StorageZoneId"])
            pullzoneid = int(d["Id"])

    storagezoneUrl = 'https://bunnycdn.com/api/storagezone/'

    try:
        r = requests.get(storagezoneUrl, headers=headers)
    except requests.ConnectionError:
        return p

    data = r.json()

    for d in data:
        if int(d["Id"]) == storageid:
            p.storage = float("{0:.2f}".format(float(d["StorageUsed"])/(1024*1024*1024)))
            p.files = int(d["FilesStored"])

    planObj = provider.models.Plan.objects.filter(provider_id=providerid)[0]
    startdate = str(planObj.startdate).split(" ")[0]
    apiUrl = 'https://bunnycdn.com/api/statistics?dateFrom=' + startdate + '&pullZone=' + str(pullzoneid)

    try:
        r = requests.get(apiUrl, headers=headers)
    except requests.ConnectionError:
        return p

    data = r.json()
    p.bandwidth = float("{0:.2f}".format(float(data["TotalBandwidthUsed"])/(1024*1024*1024)))

    return p
