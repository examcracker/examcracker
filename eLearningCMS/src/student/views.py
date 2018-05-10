from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from collections import OrderedDict
from operator import itemgetter
from django.contrib.auth import get_user_model
from . import models
from . import forms
import course
from course import algos
import provider
import re

User = get_user_model()

def getStudent(request):
    return models.Student.objects.filter(user_id=request.user.id)[0]

class showStudentHome(LoginRequiredMixin, generic.TemplateView):
    template_name = 'student_home.html'

class showStudentProfile(LoginRequiredMixin, generic.TemplateView):
    template_name = 'my_profile.html'

class showRecommendedCourses(LoginRequiredMixin, generic.TemplateView):
    template_name = 'recommended_courses.html'

class showProgress(LoginRequiredMixin, generic.TemplateView):
    template_name = 'progress.html'

class joinCourses(LoginRequiredMixin, generic.TemplateView):
    template_name = 'join_courses.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        notJoinedCourses = course.models.Course.objects.raw('SELECT * FROM course_course WHERE published = 1 and id NOT IN (SELECT course_id FROM course_enrolledcourse WHERE student_id = ' + str(studentObj.id) + ') ORDER BY created')
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
