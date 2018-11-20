from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
import course
from course import models
from provider.views import showProviderHome, getProvider
from django.forms.models import model_to_dict
from . import models
import websock
import provider

# Create your views here.

class addShowSchedule(showProviderHome):
    template_name = "addShowSchedule.html"
    http_method_names = ['get','post']

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()

        providerObj = getProvider(request)
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
                scheduleInfo['chapterName'] = chapterObj.name
                scheduleInfo['subjectName'] = chapterObj.subject
                scheduleInfo['courseName'] = course.models.Course.objects.filter(id=chapterObj.course_id)[0].name
                scheduleInfo['courseId'] = chapterObj.course_id
                scheduleInfo['eventsOccured'] = sessionsCount
                scheduleInfo['eventsRemaining'] = schedule.eventcount - sessionsCount
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
        scheduleObj.start = request.POST.get('startDate')
        scheduleObj.eventcount = request.POST.get('eventCount')
        scheduleObj.duration = request.POST.get('eventDuration')
        scheduleObj.recurafter = request.POST.get('eventRecur')

        scheduleObj.save()
        return redirect("schedule:add_show_schedule")

class startCapture(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, chapterid, *args, **kwargs):
        chapterObj = course.models.CourseChapter.objects.filter(id=chapterid)[0]
        courseObj = course.models.Course.objects.filter(id=chapterObj.course_id)[0]
        providerObj = provider.models.Provider.objects.filter(id=courseObj.provider_id)[0]

        wsclient = None
        if providerObj.id in websock.consumers.connectedConsumerClients.keys():
            wsclient = websock.consumers.connectedConsumerClients[providerObj.id]

        if wsclient:
            wsclient.startcourse(chapterid)

        return redirect("schedule:add_show_schedule")

