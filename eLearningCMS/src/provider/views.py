from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from . import models
from . import forms
import course
import datetime

def getProvider(request):
    return models.Provider.objects.filter(user_id=request.user.id)[0]

class showProviderHome(LoginRequiredMixin, generic.TemplateView):
    template_name = 'userDashBoard.html'
'''
class uploadVideo(LoginRequiredMixin, CreateView):
    template_name = 'upload_video.html'
    model = models.Session
    fields = ['name', 'video']

    def post(self, request):
        videoForm = forms.uploadVideoForm(request.POST, request.FILES)
        if videoForm.is_valid():
            sessionObj = videoForm.save(commit=False)
            sessionObj.provider = getProvider(request)
            sessionObj.save()
        videoForm.save()
        return redirect("provider:provider_home")
'''
class uploadVideo(LoginRequiredMixin, generic.TemplateView):
    template_name = "upload_video_multiple.html"
    http_method_names = ['get', 'post']

    def post(self, request):
        providerObj = getProvider(request)
        filesUploaded = request.FILES.getlist('videos')
        for file in filesUploaded:
            sessionObj = models.Session()
            sessionObj.name = file
            sessionObj.provider = providerObj
            sessionObj.video = file
            sessionObj.save()
        return redirect("provider:provider_home")

class createCourse(LoginRequiredMixin, CreateView):
    template_name = 'create_course.html'
    model = course.models.Course
    fields = ['name', 'exam', 'cost', 'duration', 'published']

    def post(self, request):
        courseForm = forms.courseCreateForm(request.POST)
        if courseForm.is_valid():
            courseObj = courseForm.save(commit=False)
            courseObj.provider = getProvider(request)
            courseObj.save()
        courseForm.save()
        return redirect("provider:provider_home")

class viewSessions(LoginRequiredMixin, generic.TemplateView):
    template_name = "view_videos.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        providerObj = getProvider(request)
        sessionList = models.Session.objects.filter(provider_id=providerObj.id)
        kwargs["sessions"] = sessionList
        return super().get(request, *args, **kwargs)

class viewCourses(LoginRequiredMixin, generic.TemplateView):
    template_name = "view_courses.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        providerObj = getProvider(request)
        courseList = course.models.Course.objects.filter(provider_id=providerObj.id)
        kwargs["courses"] = courseList
        return super().get(request, *args, **kwargs);

class courseDetail(LoginRequiredMixin, generic.TemplateView):
    template_name = 'course_detail.html'
    http_method_names = ['get', 'post']

    def get(self, request, id, *args, **kwargs):
        courseid = id
        courseObj = course.models.Course.objects.filter(id=courseid)[0]
        kwargs["course_detail"] = courseObj

        sessionsNotInCourse = models.Session.objects.raw('SELECT * FROM provider_session WHERE id NOT IN (SELECT session_id FROM course_coursepattern WHERE course_id = ' + str(courseObj.id) + ') ORDER BY uploaded')
        kwargs["excluded_sessions"] = sessionsNotInCourse

        sessionsInCourse = models.Session.objects.raw('SELECT * FROM provider_session WHERE id IN (SELECT session_id from course_coursepattern WHERE course_id = ' + str(courseObj.id) + ') ORDER BY uploaded')
        kwargs["included_sessions"] = sessionsInCourse
        return super().get(request, *args, **kwargs)

    def post(self, request, id, *args, **kwargs):
        courseid = id
        courseObj = course.models.Course.objects.filter(id=courseid)[0]
        addedVideos = request.POST.getlist('sessions[]')

        if len(addedVideos) == 0:
            courseObj.published = True
            courseObj.save()
            return redirect("provider:course_detail", id)

        totalVideos = course.models.CoursePattern.objects.filter(course_id=id)
        maxsequence = 0

        i = 0
        while i < len(totalVideos):
            obj = totalVideos[i]
            if obj.sequence > maxsequence:
                maxsequence = obj.sequence
            i = i + 1

        for video in addedVideos:
            sessionObj = models.Session.objects.filter(id=video)[0]
            coursePatternObj = course.models.CoursePattern()
            coursePatternObj.sequence = maxsequence + 1
            coursePatternObj.course = courseObj
            coursePatternObj.session = sessionObj
            coursePatternObj.save()
            maxsequence = maxsequence + 1

        return redirect("provider:course_detail", id)

class sessionDetail(LoginRequiredMixin, generic.TemplateView):
    template_name = 'video_detail.html'
    http_method_names = ['get', 'post']

    def get(self, request, id, *args, **kwargs):
        sessionid = id
        sessionObj = models.Session.objects.filter(id=sessionid)[0]
        kwargs["session_detail"] = sessionObj

        notAddedInCourse = course.models.Course.objects.raw('SELECT * FROM course_course WHERE id NOT IN (SELECT course_id FROM course_coursepattern WHERE session_id = ' + str(sessionObj.id) + ') ORDER BY created')
        kwargs["excluded_courses"] = notAddedInCourse

        addedInCourse = course.models.Course.objects.raw('SELECT * FROM course_course WHERE id IN (SELECT course_id from course_coursepattern WHERE session_id = ' + str(sessionObj.id) + ') ORDER BY created')
        kwargs["included_courses"] = addedInCourse
        return super().get(request, *args, **kwargs)

    def post(self, request, id, *args, **kwargs):
        sessionid = id
        sessionObj = models.Session.objects.filter(id=sessionid)[0]
        addedCourses = request.POST.getlist('courses[]')

        for courses in addedCourses:
            courseObj = course.models.Course.objects.filter(id=courses)[0]
            totalVideos = course.models.CoursePattern.objects.filter(course_id=courses)
            maxsequence = 0

            i = 0
            while i < len(totalVideos):
                obj = totalVideos[i]
                if obj.sequence > maxsequence:
                    maxsequence = obj.sequence
                i = i + 1

            coursePatternObj = course.models.CoursePattern()
            coursePatternObj.sequence = maxsequence + 1
            coursePatternObj.course = courseObj
            coursePatternObj.session = sessionObj
            coursePatternObj.save()

        return redirect("provider:video_detail", id)
