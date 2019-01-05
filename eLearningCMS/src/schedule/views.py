from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
import course
from course import models
from provider.views import showProviderHome, getProvider
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.http import Http404
from Crypto.Cipher import AES
from . import models
import provider
import schedule
import pusher
import pysher
import websocket
import enum
import json
import base64

PUSHER_APP_ID = "656749"
PUSHER_KEY = "3ff394e3371be28d8abd"
PUSHER_SECRET = "35f5a7cde33cd756c30d"
PUSHER_CLUSTER = "ap2"

# Commands
command_start = 0
command_stop = 1

# Status
status_start_success = 0
status_capture_started = 1
status_no_capture_started = 2
status_camera_not_detected = 3
status_stop_success = 4

class HttpResponseNoContent(HttpResponse):
    status_code = 200

# Create your views here.

def getActiveSchedules(providerId):
    scheduleObj = models.Schedule.objects.filter(provider_id=providerId)
    activeCount = 0
    for schedule in scheduleObj:
        chapterObj = course.models.CourseChapter.objects.filter(id=schedule.chapter_id)[0]
        sessions = chapterObj.sessions
        sessionsCount = 0
        if sessions != '':
            sessionsCount = len(sessions.split(','))
        if sessionsCount < schedule.eventcount:
            activeCount = activeCount+1
    return activeCount

class addShowSchedule(showProviderHome):
    template_name = "addShowSchedule.html"
    http_method_names = ['get','post']

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()

        providerObj = getProvider(request)
        locations = []
        locationObj = provider.models.System.objects.filter(provider_id=providerObj.id)
        for location in locationObj:
            locations.append(location.name)
        kwargs['locations'] = locations


        mycourses = course.models.Course.objects.raw('SELECT * from course_course WHERE provider_id = ' + str(providerObj.id) + \
                                                     ' AND id NOT IN (SELECT parent_id from course_linkcourse)')

        courseDict = []
        for c in mycourses:
            courseDetails = course.algos.getCourseDetails(c.id, False)
            courseInfo = {}
            courseInfo['name'] = c.name
            courseInfo['details'] = courseDetails
            courseDict.append(courseInfo)
        kwargs['mycourses'] = courseDict

        # Get schedule for this provider
        scheduleObj = models.Schedule.objects.filter(provider_id=providerObj.id)
        if scheduleObj :
            schedules = []
            for schedule in scheduleObj:
                scheduleInfo = model_to_dict(schedule)
                chapterObj = course.models.CourseChapter.objects.filter(id=schedule.chapter_id)[0]
                sessions = chapterObj.sessions
                sessionsCount = 0
                if sessions != '':
                    sessionsCount = len(sessions.split(','))

                scheduleInfo['id'] = schedule.id
                scheduleInfo['chapterName'] = chapterObj.name
                scheduleInfo['subjectName'] = chapterObj.subject
                scheduleInfo['courseName'] = course.models.Course.objects.filter(id=chapterObj.course_id)[0].name
                scheduleInfo['courseId'] = chapterObj.course_id
                scheduleInfo['eventsOccured'] = sessionsCount
                scheduleInfo['eventsRemaining'] = schedule.eventcount - sessionsCount
                scheduleInfo['autoPublish'] = schedule.autopublish
                schedules.append(scheduleInfo)
            kwargs['schedules'] = schedules
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()
        providerObj = getProvider(request)
        courseChapterName = request.POST.get('courseChapterName',"")
        # if this element doesnt comes, then its edit flow
        chapterid = ''
        if courseChapterName == '':
            chapterid = request.POST.get('scheduleChapterId')
        else:
            chapterid = courseChapterName.split(':')[2]
        scheduleObj = models.Schedule.objects.filter(chapter_id = chapterid)
        if not scheduleObj :
            scheduleObj = models.Schedule()
            scheduleObj.chapter_id = chapterid
            scheduleObj.provider_id = providerObj.id
        else:
            scheduleObj = scheduleObj[0]
        startDate = request.POST.get('startDate','')
        if startDate != '':
            scheduleObj.start = startDate
        scheduleObj.eventcount = request.POST.get('eventCount')
        scheduleObj.duration = request.POST.get('eventDuration')
        scheduleObj.recurafter = request.POST.get('eventRecur')
        scheduleObj.system = request.POST.get('courseLocation','')
        if request.POST.get('autoPublish'):
            scheduleObj.autopublish = True
        else:
            scheduleObj.autopublish = False

        scheduleObj.save()
        return redirect("schedule:add_show_schedule")

def createDictSchedule(scheduleObj, command):
    dictObj = {}
    dictObj["id"] = scheduleObj.id
    dictObj["command"] = command
    dictObj["start"] = str(scheduleObj.start)
    dictObj["eventcount"] = scheduleObj.eventcount
    dictObj["duration"] = scheduleObj.duration
    dictObj["recurafter"] = scheduleObj.recurafter
    dictObj["chapterid"] = scheduleObj.chapter_id
    dictObj["publish"] = scheduleObj.autopublish
    dictObj["machine"] = scheduleObj.system
    return dictObj

class startCapture(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, scheduleid, *args, **kwargs):
        scheduleObj = schedule.models.Schedule.objects.filter(id=scheduleid)[0]
        providerObj = provider.models.Provider.objects.filter(id=scheduleObj.provider_id)[0]

        pusherObj = pusher.Pusher(app_id=PUSHER_APP_ID, key=PUSHER_KEY, secret=PUSHER_SECRET, cluster=PUSHER_CLUSTER, ssl=True)
        pusherObj.trigger(str(providerObj.id), str(providerObj.id), createDictSchedule(scheduleObj, command_start))
        return redirect("schedule:add_show_schedule")

class stopCapture(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, scheduleid, *args, **kwargs):
        scheduleObj = schedule.models.Schedule.objects.filter(id=scheduleid)[0]
        providerObj = provider.models.Provider.objects.filter(id=scheduleObj.provider_id)[0]

        pusherObj = pusher.Pusher(app_id=PUSHER_APP_ID, key=PUSHER_KEY, secret=PUSHER_SECRET, cluster=PUSHER_CLUSTER, ssl=True)
        pusherObj.trigger(str(providerObj.id), str(providerObj.id), createDictSchedule(scheduleObj, command_stop))
        return redirect("schedule:add_show_schedule")

class addSystem(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        dictBody = json.loads(request.body.decode())

        encryptedClientId = base64.b64decode(dictBody["id"])
        decipher = AES.new(provider.models.aes_key, AES.MODE_CFB, provider.models.aes_iv)

        try:
            providerId = int(decipher.decrypt(encryptedClientId).decode())
        except:
            raise Http404()

        systemName = dictBody["system"]
        systemQ = provider.models.System.objects.filter(provider_id=providerId).filter(name=systemName)
        if len(systemQ) == 0:
            systemObj = provider.models.System()
            systemObj.name = dictBody["system"]
            systemObj.provider = provider.models.Provider.objects.filter(id=providerId)[0]
            systemObj.save()

        return HttpResponseNoContent()

class captureState(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, scheduleid, *args, **kwargs):
        scheduleObj = models.Schedule.objects.filter(id=scheduleid)
        if len(scheduleObj) == 0:
            raise Http404()
        scheduleObj = scheduleObj[0]

        dictBody = json.loads(request.body.decode())

        encryptedClientId = base64.b64decode(dictBody["id"])
        decipher = AES.new(provider.models.aes_key, AES.MODE_CFB, provider.models.aes_iv)

        try:
            providerId = int(decipher.decrypt(encryptedClientId).decode())
        except:
            raise Http404()

        if scheduleObj.provider_id != providerId:
            raise Http404()

        state = dictBody["state"]
        scheduleObj.running = state
        scheduleObj.save()

        return HttpResponseNoContent()
