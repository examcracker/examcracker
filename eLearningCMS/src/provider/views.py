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
    providerObj = models.Provider.objects.filter(user_id=request.user.id)
    if providerObj.exists():
      return providerObj[0]
    else:
      return providerObj

class showProviderHome(LoginRequiredMixin, generic.TemplateView):
    template_name = 'provider_home.html'

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

class createCourse(LoginRequiredMixin, generic.TemplateView):
    template_name = 'create_course.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        providerObj = getProvider(request)
        courseId = request.POST.get("courseId",'')
        courseObj = course.models.Course()
        kwargs["allExams"] = course.models.EXAM_CHOICES
        if courseId != '':
          courseObj = course.models.Course.objects.filter(id=courseId)[0]
          kwargs["editCourse"] = courseObj
        return super().get(request, *args, **kwargs)

    def post(self, request,*args, **kwargs):
        cId = request.POST.get('courseId','')
        kwargs["allExams"] = course.models.EXAM_CHOICES
        courseObj = course.models.Course()
        kwargs["courseId"] = cId
        if cId != '':
          courseObj = course.models.Course.objects.filter(id=cId)[0]
          kwargs["editCourse"] = courseObj
        courseName = request.POST.get('courseName','')
        # This means , this is Edit course flow.
        if courseName == '':
            return super().get(request, *args, **kwargs)
        # no need to validate, validation already done in html form
        courseObj.name = courseName
        courseObj.description=request.POST.get('courseDescription','')
        courseObj.exam=request.POST.get("courseExam",'')
        courseObj.provider=getProvider(request)
        courseObj.cost=request.POST.get("courseCost",'')
        courseObj.duration=request.POST.get("courseDuration",'')
        courseObj.save()
        kwargs["editCourse"] = courseObj
        return super().get(request, *args, **kwargs)
        
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
        if providerObj:
            kwargs["providerId"] = providerObj.id
        return super().get(request, *args, **kwargs)
