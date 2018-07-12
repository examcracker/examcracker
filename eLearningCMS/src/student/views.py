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
from course import algos
import provider
import re
import profiles
import payments
from math import ceil

User = get_user_model()

def getStudent(request):
    return models.Student.objects.filter(user_id=request.user.id)[0]

class showStudentHome(LoginRequiredMixin, generic.TemplateView):
    template_name = 'student_home.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        category = "ALL Courses"
        allCourses = course.models.Course.objects.raw('SELECT * FROM course_course WHERE published = True ORDER BY created')
        kwargs["allCourses"] = allCourses
        kwargs["category"] = category
        return super().get(request, *args, **kwargs)

class StudentProfile(profiles.views.MyProfile):
    template_name = 'student_profile.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return redirect("student:my_profile")

class showRecommendedCourses(LoginRequiredMixin, generic.TemplateView):
    template_name = 'recommended_courses.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        notJoinedCourses = course.models.Course.objects.raw('SELECT * FROM course_course WHERE published = True and id NOT IN (SELECT course_id FROM course_enrolledcourse WHERE student_id = ' + str(studentObj.id) + ') ORDER BY created')
        kwargs["remaining_courses"] = notJoinedCourses
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

class joinCourses(LoginRequiredMixin, generic.TemplateView):
    template_name = 'join_courses.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        notJoinedCourses = course.models.Course.objects.raw('SELECT * FROM course_course WHERE published = True and id NOT IN (SELECT course_id FROM course_enrolledcourse WHERE student_id = ' + str(studentObj.id) + ') ORDER BY created')
        kwargs["remaining_courses"] = notJoinedCourses
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        joinedCourses = request.POST.getlist('courses[]')

        for courses in joinedCourses:
            courseObj = course.models.Course.objects.filter(id=courses)[0]
            enrolledCourseObj = course.models.EnrolledCourse()
            enrolledCourseObj.student = studentObj
            enrolledCourseObj.course = courseObj
            enrolledCourseObj.save()

        return redirect("student:join_courses")

class myCourses(LoginRequiredMixin, generic.TemplateView):
    template_name = 'my_courses.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        myCourses = course.models.Course.objects.raw('SELECT * FROM course_course WHERE id IN (SELECT course_id FROM course_enrolledcourse WHERE student_id = ' + str(studentObj.id) + ')')
        kwargs["courses"] = myCourses
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

        present = len(course.models.EnrolledCourse.objects.filter(course_id=courseid, student_id=studentObj.id))
        if present == 0:
            kwargs["not_joined"] = True
        return super().get(request, id, *args, **kwargs)

    def post(self, request, id, *args, **kwargs):
        courseid = id
        courseObj = course.models.Course.objects.filter(id=courseid)[0]

        studentObj = models.Student.objects.filter(user_id=request.user.id)[0]

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
        enrolledCourseObj = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id)
        if len(enrolledCourseObj) > 0:
            courseDictMap["myCourse"] = True
        for enrolledCourse in enrolledCourseObj:
            courseDict = {}
            courseid = enrolledCourse.course_id
            durationCompleted = 0
            totalDuration = 0
            for s in enrolledCourse.sessions:
                sessionObj = provider.models.Session.objects.filter(id=s)[0]
                durationCompleted = durationCompleted + sessionObj.duration

            courseObj = course.models.Course.objects.filter(id=courseid)[0]
            courseDict['name'] = courseObj.name
            courseDict['chartTitle'] = 'Chapter wise distribution'
            courseDict['duration'] = courseObj.duration
            courseDict['progressbarShow'] = True
            courseChaptersObj=[]
            courseChapters = course.models.CourseChapter.objects.filter(course_id=courseid)
            sessions_list = [v for v in enrolledCourse.sessions]
            chaptersArray = []
            chaptersArray.append(['Topics', 'topics distribution per chapter'])

            for courseChapter in courseChapters:
                chapter = {}
                chapter['name'] = courseChapter.name
                durationChapterCompleted = 0
                durationChapterTotal = 0

                for s in courseChapter.sessions:
                    sessionObj = provider.models.Session.objects.filter(id=s)[0]
                    durationChapterTotal = durationChapterTotal + sessionObj.duration
                    if(s in sessions_list):
                        durationChapterCompleted = durationChapterCompleted + sessionObj.duration

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
