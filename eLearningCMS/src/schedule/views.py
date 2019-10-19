from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.conf import settings
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
import student
import cdn
from django.db.models import Q

from access.views import parse_user_agents

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

# schedule states
STOPPED = 0
RUNNING = 1
UPLOADING = 2

# Macros for Storage locations
DO = 1
BUNNY = 2

class HttpResponseNoContent(HttpResponse):
    status_code = 200

# Create your views here.
# Authenticate that provider has rights to publish live streaming
class on_publish(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        #return HttpResponse(status=404)

        scheduleid = request.GET.get('scheduleid', '')
        providerid = request.GET.get('providerid', '')
        #sessionKey = request.GET.get('sessionKey', '')
        if scheduleid == '' or providerid == '':
            return HttpResponse(status=404)
        scheduleObj = models.Schedule.objects.filter(id=scheduleid,provider_id=providerid)
        if not scheduleObj:
            return HttpResponse(status=404)
        scheduleObj = scheduleObj[0]
        # clear stream_access table for this schedule id
        schedule_liveaccessObj = models.Schedule_liveaccess.objects.filter(schedule_id=scheduleObj.id)
        if schedule_liveaccessObj:
            schedule_liveaccessObj.delete()
        return HttpResponse(status=201)

# Authenticate live streaming view by user
class on_play(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        #return HttpResponse(status=201)
        # this is client ip received from nginx
        ipaddr = request.GET.get('addr', '')
        scheduleid = request.GET.get('scheduleid', '')
        providerid = request.GET.get('providerid', '')
        studentid = request.GET.get('studentid', '')
        userIP = request.GET.get('userIP', '')
        
        if scheduleid == '' and studentid == '' and providerid == '':
            scheduleObj = models.Schedule.objects.filter(streamkey=ipaddr)
            if scheduleObj:
                return HttpResponse(status=201)
            schedule_liveaccessObj = models.Schedule_liveaccess.objects.filter(nginxip=ipaddr)
            if schedule_liveaccessObj:
                return HttpResponse(status=201)
        elif studentid != '' and scheduleid != '' and userIP != '':
            schedule_liveaccessObj = models.Schedule_liveaccess.objects.filter(schedule_id=scheduleid,student_id=studentid)
            if not schedule_liveaccessObj:
                return HttpResponse(status=404)
            schedule_liveaccessObj = schedule_liveaccessObj[0]
            if schedule_liveaccessObj.nginxip == ipaddr and schedule_liveaccessObj.ip == userIP:
                return HttpResponse(status=201)
            if schedule_liveaccessObj.nginxip == '':
                schedule_liveaccessObj.nginxip = ipaddr
                schedule_liveaccessObj.save()
                return HttpResponse(status=201)
        elif providerid != '' and scheduleid != '' and userIP != '':
            scheduleObj = models.Schedule.objects.filter(id=scheduleid,provider_id=providerid)
            if not scheduleObj:
                return HttpResponse(status=404)
            scheduleObj = scheduleObj[0]
            if scheduleObj.streamkey == ipaddr:
                return HttpResponse(status=201)
            if scheduleObj.streamkey == '':
                scheduleObj.streamkey = ipaddr
                scheduleObj.save()
                return HttpResponse(status=201)
        return HttpResponse(status=404)

# Authenticate live streaming view by user
class on_publish_done(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        return HttpResponse(status=201)

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

def isAnyEventLive(request):
    scheduleObj = models.Schedule.objects.filter(running=1)
    if not scheduleObj:
        return False
    if request.user.is_staff:
        # Get Live events of Scheduled courses
        providerObj = getProvider(request)
        scheduleObj = scheduleObj.filter(provider_id=providerObj.id)
    else:
        # Get live events of enrolled courses
        scheduleObj = scheduleObj.filter(autopublish=True)
        studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
        courseIds = course.algos.getEnrolledCourseIds(request)
        enrolledCourseObj = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id,active=True,course_id__in=courseIds)
        chaptersList = []
        for ec in enrolledCourseObj:
            if ec.chapteraccess == '':
                courseChapterObj = course.models.CourseChapter.objects.filter(course_id=ec.course_id)
                for cco in courseChapterObj:
                    chaptersList.append(cco.id)
            else:
                allowedModules = ec.chapteraccess.split(',')
                allowedModulesInt = [int(i) for i in allowedModules]
                chaptersList.extend(allowedModulesInt)
            #courseChapterObj = course.models.CourseChapter.objects.filter(Q(course_id__in=enrolledCourseObj.values('course_id'))).values('id')
        scheduleObj = scheduleObj.filter(Q(chapter_id__in=chaptersList))

    if scheduleObj :
        return True
    return False

class showLiveEvents(provider.views.showProviderHome,LoginRequiredMixin,generic.TemplateView):
    template_name = "showLiveEvents.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        
        scheduleObj = models.Schedule.objects.filter(running=1)
        kwargs["disableKeys"] = "true"
        if not scheduleObj:
            return super().get(request, *args, **kwargs)
        if request.user.is_staff:
            # Get Live events of Scheduled courses
            providerObj = getProvider(request)
            scheduleObj = scheduleObj.filter(provider_id=providerObj.id)
        else:
            # Get live events of enrolled courses
            scheduleObj = scheduleObj.filter(autopublish=True)
            studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
            courseIds = course.algos.getEnrolledCourseIds(request)
            enrolledCourseObj = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id,active=True,course_id__in=courseIds)
            chaptersList = []
            for ec in enrolledCourseObj:
                if ec.chapteraccess == '':
                    courseChapterObj = course.models.CourseChapter.objects.filter(course_id=ec.course_id)
                    for cco in courseChapterObj:
                        chaptersList.append(cco.id)
                else:
                    allowedModules = ec.chapteraccess.split(',')
                    allowedModulesInt = [int(i) for i in allowedModules]
                    chaptersList.extend(allowedModulesInt)
            #courseChapterObj = course.models.CourseChapter.objects.filter(Q(course_id__in=enrolledCourseObj.values('course_id'))).values('id')
            scheduleObj = scheduleObj.filter(Q(chapter_id__in=chaptersList))

        if scheduleObj :
            schedules = []
            kwargs["live"] = 'on'
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
                schedules.append(scheduleInfo)
            kwargs['schedules'] = schedules
        return super().get(request, *args, **kwargs)

class addShowSchedule(showProviderHome):
    template_name = "addShowSchedule.html"
    http_method_names = ['get','post']

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()

        providerObj = getProvider(request)
        kwargs["disableKeys"] = "false"
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
                scheduleInfo['encrypt'] = schedule.autopublish
                scheduleInfo['start'] = schedule.start
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

        '''
        if request.POST.get('encrypt'):
            scheduleObj.encrypted = True
        else:
            scheduleObj.encrypted = False
        '''
        scheduleObj.encrypted = True

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
    dictObj["encrypted"] = scheduleObj.encrypted
    dictObj["machine"] = scheduleObj.system
    dictObj["mediaServer"] = settings.MEDIA_SERVER_IP
    dictObj["mediaServerApp"] = settings.MEDIA_SERVER_APP
    dictObj["live"] = True
    dictObj["dokey"] = settings.DIGITAL_OCEAN_SPACE_KEY
    dictObj["dokeysecret"] = settings.DIGITAL_OCEAN_SPACE_KEY_SECRET

    drm_deatils = cdn.views.getClearKey()
    dictObj["drmkeyid"] = drm_deatils['KeyID']
    dictObj["drmkey"] = drm_deatils['Key']
    dictObj["multiBitRate"] = False
    dictObj['email'] = settings.EMAIL_HOST_USER
    dictObj['email_password'] = settings.EMAIL_HOST_PASSWORD

    return dictObj

def getStreamUrl(streamname):
    #hlsurl = 'https://' + settings.MEDIA_SERVER_SUB_DOMAIN + ':' + settings.MEDIA_SERVER_HTTPS_PORT + '/hls/' + streamname + '.m3u8'
    url = 'https://' + settings.MEDIA_SERVER_SUB_DOMAIN + '/dash/' + streamname + '.mpd'
    return url

class playStream(LoginRequiredMixin, generic.TemplateView):
    template_name = "playSchedule.html"
    http_method_names = ['get']

    def check(self, kwargs):
        for tag in course.tags.playSessionEncTags:
            if not tag in kwargs:
                kwargs[tag] = ""

    def get(self, request, scheduleid, *args, **kwargs):
        scheduleObj = schedule.models.Schedule.objects.filter(id=scheduleid)
        OFUSCATE_JW = True
        kwargs["disableKeys"] = "true"
        if not scheduleObj:
            raise Http404()
        if settings.DEBUG:
            kwargs["debug"] = "on"
        else:
            kwargs["debug"] = "off"
        if OFUSCATE_JW:
            kwargs["offuscate"] = True
        else:
            kwargs["offuscate"] = False
        
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[-1].strip()
        #http_x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        #ip2 = request.META.get('REMOTE_ADDR')
        #print('http_x_forwarded_for is: ' + http_x_forwarded_for)
        #print ('ip2 is : ' + ip2)
        scheduleObj = scheduleObj[0]
        userString = '?'
        courseChapterObj = course.models.CourseChapter.objects.filter(id=scheduleObj.chapter_id)
        if request.user.is_staff:
            courseChapterObj = courseChapterObj[0]
            # Get Live events of Scheduled courses
            providerObj = getProvider(request)
            if scheduleObj.provider_id != providerObj.id:
                raise Http404()
            
            scheduleObj.streamkey = ''
            scheduleObj.save()
            userString = userString + 'providerid='+str(providerObj.id) + '&'
            kwargs["isOwner"] = 'yes'
            kwargs["courseid"] = courseChapterObj.course_id
        else:
            # check if student is enrolled for this schedule
            if not courseChapterObj:
                raise Http404()
            courseChapterObj = courseChapterObj[0]

            studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
            courseIds = course.algos.getEnrolledCourseIds(request)
            enrolledCourseObj = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id,course_id=courseChapterObj.course_id,active=True)
            enrolledCourseObj = enrolledCourseObj.filter(course_id__in=courseIds)
            if not enrolledCourseObj:
                raise Http404()
            enrolledCourseObj = enrolledCourseObj[0]
            kwargs["enrolledcourseid"] = enrolledCourseObj.id
            kwargs["isOwner"] = 'no'
            # dont do device verification if restricted viewing for student is set
            if enrolledCourseObj.viewhours > 0:
                kwargs["disableaccess"] = True
            else:
                kwargs["disableaccess"] = False

            #check view hours and alloted hours before proceed further
            courseObj = course.models.Course.objects.filter(id=courseChapterObj.course_id)[0]
            viewMinutes,allotedHours = student.views.getStudentViewAllotedHoursProviderWise(studentObj.id,courseObj.provider_id)
            if allotedHours > 0 and viewMinutes >= allotedHours*60:
                raise Http404()
            userString = userString+'studentid='+str(studentObj.id)+'&'

            # delete all access enteries for this student for this schedule
            schedule_liveaccessObj = models.Schedule_liveaccess.objects.filter(schedule_id=scheduleObj.id,student_id=studentObj.id)
            schedule_liveaccessObj.delete()

            # add new IP entry for this student in schedule access table
            schedule_liveaccessObjNew = models.Schedule_liveaccess()
            schedule_liveaccessObjNew.ip = ip
            schedule_liveaccessObjNew.nginxip = ''
            schedule_liveaccessObjNew.schedule_id = scheduleObj.id
            schedule_liveaccessObjNew.student_id = studentObj.id
            schedule_liveaccessObjNew.save()
            # store student stats in table
            deviceinfo = parse_user_agents(request)
            student.views.fillStudentPlayStats(studentObj.id,-1,ip,request.user.email,deviceinfo)
        #HttpResponse.set_cookie('GyaanHiveIP', ip)
        kwargs["isLive"] = "true"
        kwargs["signedurl"] = getStreamUrl(scheduleObj.streamname) + userString + 'scheduleid=' + str(scheduleObj.id)+'&userIP='+ ip
        kwargs["liveUrl"] = getStreamUrl(scheduleObj.streamname) + userString + 'scheduleid=' + str(scheduleObj.id)+'&userIP='+ ip
        kwargs["user_email"] = request.user.email
        kwargs["userip"] = ip

        self.check(kwargs)

        response = super().get(request, scheduleid, *args, **kwargs)
        response.set_cookie('GyaanHiveIP', ip)
        return response

class startCapture(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, scheduleid, *args, **kwargs):
        scheduleObj = schedule.models.Schedule.objects.filter(id=scheduleid)[0]
        providerObj = provider.models.Provider.objects.filter(id=scheduleObj.provider_id)[0]

        pusherObj = pusher.Pusher(app_id=settings.PUSHER_APP_ID, key=settings.PUSHER_KEY, secret=settings.PUSHER_SECRET, cluster=settings.PUSHER_CLUSTER, ssl=True)
        scheduleDict = createDictSchedule(scheduleObj, command_start)
        
        # Cloud storage names and flags whether to upload to them or not
        # some hard coded values for trial only
        scheduleDict['bucketname'] = providerObj.bucketname
        bnStorage = 'gyaanhive' + str(providerObj.id)
        storageObj = provider.models.Storage.objects.filter(name=bnStorage)
        scheduleDict['DoUpload'] = False
        if storageObj:
            storageObj = storageObj[0]
            scheduleDict['bunnyCDNStorageName'] = storageObj.name
            scheduleDict['bunnyUpload'] = True
            scheduleDict['bunnyCDNStoragePassword'] = storageObj.key
            scheduleDict['bunnyUpload'] = True
            scheduleDict['primary'] = BUNNY
        else:   
            scheduleDict['bunnyUpload'] = False
            scheduleDict['DoUpload'] = True
            scheduleDict['primary'] = DO
        pusherObj.trigger(str(providerObj.id), str(providerObj.id), scheduleDict)
        return redirect("schedule:add_show_schedule")

class stopCapture(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, scheduleid, *args, **kwargs):
        scheduleObj = schedule.models.Schedule.objects.filter(id=scheduleid)[0]
        providerObj = provider.models.Provider.objects.filter(id=scheduleObj.provider_id)[0]

        pusherObj = pusher.Pusher(app_id=settings.PUSHER_APP_ID, key=settings.PUSHER_KEY, secret=settings.PUSHER_SECRET, cluster=settings.PUSHER_CLUSTER, ssl=True)
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
        if 'streamName' in dictBody:
            scheduleObj.streamname = dictBody["streamName"]
        if 'streamKey' in dictBody:
            scheduleObj.streamkey = dictBody["streamKey"]
        scheduleObj.save()
        return HttpResponseNoContent()

class deleteSchedule(addShowSchedule):
    template_name="addShowSchedule.html"
    http_method_names = ['get']

    def get(self, request, scheduleid, *args, **kwargs):
        scheduleObj = schedule.models.Schedule.objects.filter(id=scheduleid)
        providerObj = getProvider(request)
        if scheduleObj[0].provider_id != providerObj.id:
            raise Http404()
        if scheduleObj:
            scheduleObj.delete()
        return redirect("schedule:add_show_schedule")
