from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from . import models
from . import forms
import course

def getProvider(request):
    return models.Provider.objects.filter(user_id=request.user.id)[0]

class showProviderHome(LoginRequiredMixin, generic.TemplateView):
    template_name = 'provider_home.html'

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

def viewCourses(request):
    loggedinuser = request.user
    providerObj = models.Provider.objects.filter(id=loggedinuser.id)[0]
    courseList = course.models.Course.objects.filter(provider_id=providerObj.id)
    return render(request, "view_courses.html", {'courses' : courseList})


