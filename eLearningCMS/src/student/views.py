from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from django.urls import reverse
from collections import OrderedDict
from operator import itemgetter
from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.http import Http404
from . import models
from . import forms
import course
#from course import algos
import provider
import re
import profiles
import payments
import notification
from math import ceil
User = get_user_model()
from schedule.views import isAnyEventLive
from datetime import datetime,timedelta

def getStudent(request):
    studentObj = models.Student.objects.filter(user_id=request.user.id)
    if studentObj.exists():
        return studentObj[0]
    else:
        return studentObj

def getStudentViewAllotedHoursProviderWise(studentid,providerid):
    providerCourses = course.models.Course.objects.filter(provider_id=providerid)
    myCourses = course.models.EnrolledCourse.objects.filter(student_id=studentid,course_id__in=providerCourses.values('id'),active=True)
    if not myCourses:
        return -1,-1
    viewMinutes = 0
    allotedHours = 0
    for c in myCourses:
        allotedHours = max(c.viewhours,allotedHours)
        viewMinutes = viewMinutes + c.completedminutes
    return int(viewMinutes),allotedHours


class showStudentHome(LoginRequiredMixin, generic.TemplateView):
    template_name = 'student_home.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        notifications = (notification.models.UserNotification.objects.filter(user=request.user.id))
        unseenNotifications = len(notifications.filter(saw=0))
        # set total count of notifications
        kwargs["notificationsCount"] = unseenNotifications
        notifications = notifications.filter(saw=False)
        kwargs["notifications"] = reversed(notifications)
        studentObj = getStudent(request)
        courseIds = course.algos.getEnrolledCourseIds(request)
        myCourses = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id,active=True)
        myCourses = myCourses.filter(course_id__in=courseIds)
        kwargs["courses"] = len(myCourses)
        viewMinutes = 0
        for c in myCourses:
            viewMinutes = viewMinutes + c.completedminutes
        kwargs["viewMinutes"] = int(viewMinutes)
        
        if isAnyEventLive(request):
            kwargs['live'] = 'on'
        return super().get(request, *args, **kwargs)

class StudentProfile(profiles.views.MyProfile):
    template_name = 'student_profile.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        notifications = (notification.models.UserNotification.objects.filter(user=request.user.id))
        # set total count of notifications
        kwargs["notificationsCount"] = len(notifications)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return redirect("student:my_profile")

class showRecommendedCourses(LoginRequiredMixin, generic.TemplateView):
    template_name = 'recommended_courses.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        notJoinedCourses = course.models.Course.objects.raw('SELECT * FROM course_course WHERE published = 1 and public = 1 and id NOT IN (SELECT course_id FROM course_enrolledcourse WHERE student_id = ' + str(studentObj.id) + ') ORDER BY created')
        kwargs["remaining_courses"] = course.algos.getCourseDetailsForCards(request, notJoinedCourses)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        courseid = request.POST.get('course')
        courseObj = course.models.Course.objects.filter(id=courseid)[0]

        cart = payments.models.Cart()
        cart.student = studentObj
        cart.course = courseObj

        if "join" in request.POST:
            cart.checkout = True
            cart.save()
            query_dictionary = QueryDict('', mutable=True)
            query_dictionary.update({'id': courseid})
            url = '{base_url}?{querystring}'.format(base_url=reverse("payments:process"),
                                                querystring=query_dictionary.urlencode())
            return redirect(url)

        if "add" in request.POST:
            cart.save()
            url = "payments:my_cart"
            return redirect(url)

class myCourses(LoginRequiredMixin, generic.TemplateView):
    template_name = 'my_courses.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        #myCourses = course.models.Course.objects.raw('SELECT * FROM course_course WHERE id IN (SELECT course_id FROM course_enrolledcourse WHERE student_id = ' + str(studentObj.id) + ')')
        myEnrolledCourses = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id,active=True)
        courseIds = course.algos.getEnrolledCourseIds(request)
        myEnrolledCourses = myEnrolledCourses.filter(course_id__in=courseIds)
        myCourses = course.models.Course.objects.filter(id__in=myEnrolledCourses.values('course_id'))
        kwargs["courses"] = course.algos.getCourseDetailsForCards(request, myCourses)
        return super().get(request, *args, **kwargs)

class courseDetails(LoginRequiredMixin, generic.TemplateView):
    template_name = 'course_details.html'
    http_method_names = ['get', 'post']

    def get(self, request, id, *args, **kwargs):
        courseid = id
        courseObj = course.models.Course.objects.filter(id=courseid)[0]
        kwargs["course_detail"] = courseObj

        studentObj = models.Student.objects.filter(user_id=request.user.id)[0]

        sessionsInCourse = provider.models.Session.objects.raw('SELECT * FROM provider_session WHERE id IN (SELECT session_id from course_coursepattern WHERE course_id = ' + str(courseObj.id) + ') ORDER BY uploaded')
        kwargs["included_sessions"] = sessionsInCourse
        courseIds = course.algos.getEnrolledCourseIds(request)
        myEnrolledCourses = course.models.EnrolledCourse.objects.filter(course_id=courseid, student_id=studentObj.id,active=True)
        myEnrolledCourses = myEnrolledCourses.objects.filter(course_id__in=courseIds)
        #present = len(course.models.EnrolledCourse.objects.filter(course_id=courseid, student_id=studentObj.id,active=True))
        present = len(myEnrolledCourses)
        if present == 0:
            kwargs["not_joined"] = True
        return super().get(request, id, *args, **kwargs)

    def post(self, request, id, *args, **kwargs):
        courseid = id
        courseObj = course.models.Course.objects.filter(id=courseid)[0]

        studentObj = models.Student.objects.filter(user_id=request.user.id)[0]
        # sudomain not done
        enrolledCourseObj = course.models.EnrolledCourse()
        enrolledCourseObj.student = studentObj
        enrolledCourseObj.course = courseObj
        enrolledCourseObj.save()

        return redirect("student:course_details", id)

class sessionDetails(LoginRequiredMixin, generic.TemplateView):
    template_name = 'video_details.html'
    http_method_names = ['get']

    def get(self, request, id, *args, **kwargs):
        sessionid = id
        sessionObj = provider.models.Session.objects.filter(id=sessionid)[0]
        kwargs["session_detail"] = sessionObj
        return super().get(request, id, *args, **kwargs)

class searchCourses(LoginRequiredMixin, generic.TemplateView):
    template_name = 'search_courses.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        kwargs["exams"] = course.algos.getExams()
        providerList = User.objects.filter(is_staff=1)
        kwargs["providers"] = providerList
        kwargs["search"] = "Search your Course"
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        searchtext = request.POST.get('search_course')
        exam = request.POST.get('examlist')
        providerstr = request.POST.get('providerlist')
        userObj = User.objects.filter(name=providerstr)[0]
        providerObj = provider.models.Provider.objects.filter(user_id=userObj.id)[0]

        courseList = course.algos.searchCourses(searchtext, providerObj.id, exam)
        examList = course.algos.getExams()
        providerList = User.objects.filter(is_staff=1)
        return render(request, self.template_name, {"courses" : courseList, "exams" : examList, "providers" : providerList, "search" : searchtext})

class showProgress(LoginRequiredMixin, generic.TemplateView):
    template_name = 'progress.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        courseDictMap = {}
        courseDictArray = []
        courseDictMap["myCourse"] = False

        enrolledCourseObj = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id,active=True)
        courseIds = course.algos.getEnrolledCourseIds(request)
        enrolledCourseObj = enrolledCourseObj.filter(course_id__in=courseIds)
        if len(enrolledCourseObj) > 0:
            courseDictMap["myCourse"] = True

        for enrolledCourse in enrolledCourseObj:
            courseDict = {}
            courseid = enrolledCourse.course_id
            durationCompleted = 0
            totalDuration = 0
            sessions_list = course.algos.strToIntList(enrolledCourse.sessions)

            for s in sessions_list:
                sessionObj = provider.models.Session.objects.filter(id=s)[0]
                durationCompleted = durationCompleted + sessionObj.duration

            courseObj = course.models.Course.objects.filter(id=courseid)[0]
            courseDict['name'] = courseObj.name
            courseDict['chartTitle'] = 'Chapter wise distribution'
            courseDict['duration'] = courseObj.duration
            courseDict['progressbarShow'] = True
            courseChaptersObj=[]
            courseChapters = course.models.CourseChapter.objects.filter(course_id=courseid)
            chaptersArray = []
            chaptersArray.append(['Topics', 'topics distribution per chapter'])

            for courseChapter in courseChapters:
                chapter = {}
                chapter['name'] = courseChapter.name
                durationChapterCompleted = 0
                durationChapterTotal = 0

                chapterSessionList = course.algos.strToIntList(courseChapter.sessions)
                publishedList = course.algos.strToBoolList(courseChapter.published)
                totalSessions = len(chapterSessionList)

                i = 0
                while i < totalSessions:
                    s = chapterSessionList[i]
                    if not publishedList[i]:
                        i=i+1
                        continue
                    sessionObj = provider.models.Session.objects.filter(id=s)[0]
                    durationChapterTotal = durationChapterTotal + sessionObj.duration
                    if(s in sessions_list):
                        durationChapterCompleted = durationChapterCompleted + sessionObj.duration
                    i=i+1

                totalDuration = totalDuration + durationChapterTotal

                chapter['duration'] = durationChapterTotal
                chapter['session_count'] = len(courseChapter.sessions)
                if durationChapterTotal > 0:
                    chapter['progress'] = durationChapterCompleted*100/durationChapterTotal
                else:
                    chapter['progress'] = 0
                courseChaptersObj.append(chapter)
                chapterArray = []
                chapterArray.append(chapter['name'])
                chapterArray.append(chapter['duration'])
                chaptersArray.append(chapterArray)
            courseDict['chapters'] = courseChaptersObj
            if totalDuration > 0:
                courseDict['progress'] = ceil(durationCompleted*100/totalDuration)
            else:
                courseDict['progress'] = 0
            courseDict['piechartArray'] = chaptersArray
            courseDictArray.append(courseDict)
        courseDictMap["outertemplateArray"] = courseDictArray
        kwargs["course_overview"] = courseDictMap

        return super().get(request, *args, **kwargs)

class VerifyEmail(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']
    template_name = "verify_email.html"

    def get(self, request, slug, *args, **kwargs):
        profileObj = profiles.models.Profile.objects.filter(user_id=request.user.id)[0]

        if str(profileObj.slug) != str(slug):
            raise Http404()

        if not profileObj.email_verified:
            profileObj.email_verified = True
            profileObj.save()

        return super().get(request, *args, **kwargs)

class view_hours(LoginRequiredMixin, generic.TemplateView):
    template_name = 'view_hours.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        if not studentObj:
            raise Http404()
        sd = course.algos.getSubDomain(request)
        subDomainObj = provider.models.Subdomain.objects.filter(subdomain = sd)
        providerObjs = provider.models.Provider.objects.all()
        if subDomainObj:
            subDomainObj = subDomainObj[0]
            providerObjs = providerObjs.filter(id=subDomainObj.provider_id)
        viewHoursProviderWise = []
        for providerObj in providerObjs:
            providerInfo = {}
            viewMinutes,allotedHours = getStudentViewAllotedHoursProviderWise(studentObj.id,providerObj.id)
            if viewMinutes == -1:
                continue
            providerUser = User.objects.filter(id=providerObj.user_id)[0]
            providerInfo['alloted_hours'] = allotedHours
            providerInfo['completed_mins'] = viewMinutes

            providerInfo['provider_name'] = providerUser.name
            viewHoursProviderWise.append(providerInfo)
        kwargs["viewHoursProviderWise"] = viewHoursProviderWise
        return super().get(request, *args, **kwargs)

def fillStudentPlayStats(studentid,sessionid,user_ip,user_email,device):
    # keep only last 5 days data
    return
    statsObj = models.StudentPlayStats.objects.filter(student_id=studentid)
    if statsObj:
        # get those objects which are older then 5 days
        now = datetime.now()
        last7days = now - timedelta(days=5)
        statsObj = statsObj.filter(date__lte = last7days)
        statsObj.delete()

    statsObj = models.StudentPlayStats()
    statsObj.student_id = studentid
    statsObj.ipaddress = user_ip
    #statsObj.session_id = sessionid
    # sessionid = -1 for live
    if sessionid != -1:
        sessionObj = provider.models.Session.objects.filter(id=sessionid)
        statsObj.sessionname = sessionObj[0].name
    else:
        statsObj.sessionname = "Live"
    browser = device["browser"]
    devicetype = device["device_type"]
    deviceinfo = 'Browser = ' + browser + '  and device = ' + devicetype
    statsObj.deviceinfo = deviceinfo
    statsObj.save()