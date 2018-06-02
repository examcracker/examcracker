from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from . import models
from django.http import JsonResponse

from . import forms
import course
import datetime
import pdb

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
        #pdb.set_trace()
        videoForm = forms.uploadFilesForm(self.request.POST,self.request.FILES)
        if videoForm.is_valid():
            sessionObj = videoForm.save(commit=False)
            sessionObj.provider = getProvider(request)
            sessionObj.name = sessionObj.video.name
            sessionObj.save()
            videoForm.save()
            data = {'is_valid': True, 'videoId': sessionObj.id, 'videoName': sessionObj.name}
            return JsonResponse(data)
        else:
            data = {'is_valid': False}
            return JsonResponse(data)

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
            kwargs["course_detail"] = course.algos.getCourseDetails(courseId,0)
        return super().get(request, *args, **kwargs)

    def post(self, request,*args, **kwargs):
        isCourseContent = request.POST.get('isCourseContent','')
        courseId = request.POST.get('courseId','')
        courseObj = course.models.Course()
        if courseId != '':
            kwargs["courseId"] = courseId
            courseObj = course.models.Course.objects.filter(id=courseId)[0]
            kwargs["editCourse"] = courseObj
            kwargs["course_detail"] = course.algos.getCourseDetails(courseId,0)
        kwargs["allExams"] = course.models.EXAM_CHOICES
        providerObj = getProvider(request)

        # check if course content flow
        if isCourseContent != '':
            #return super().get(request, *args, **kwargs)
            # auto writing chapter names
            pdb.set_trace()
            course.models.CourseChapter.objects.filter(course_id=courseId).delete()
            kwargs["course_detail"] = course.algos.getCourseDetails(courseId,0)
            if 'lcids' not in request.POST:
                return super().get(request, *args, **kwargs)
            #addedChapters = request.POST.getlist('cd[]')
            lcids = request.POST.getlist('lcids')
            if len(lcids) > 0:
                cpPrefix = 'Chapter '              
                i = 0
                while i < len(lcids):
                    i=i+1
                    chapterObj = course.models.CourseChapter()
                    chapterObj.name = cpPrefix + str(i)
                    chapterObj.course = courseObj
                    chapterObj.sequence = i
                    # first get and save files into provider_session db
                    sessionsIdArr = []
                    publishedArr = []
                    # get session ids here
                    lcVar = 'lec['+str(i)+'][]'
                    if lcVar in request.POST:
                        filesUploaded = request.POST.getlist(lcVar)
                        for sessionIds in filesUploaded:
                            sessionsIdArr.append(sessionIds)
                            publishedArr.append(True)
                    chapterObj.sessions=sessionsIdArr
                    chapterObj.published=publishedArr
                    chapterObj.save()
            kwargs["course_detail"] = course.algos.getCourseDetails(courseId,0)
            return super().get(request, *args, **kwargs)

        
        # try to segregate the procs for course description creation and 
        # course content creation
        courseName = request.POST.get('courseName','')
        # check if Edit course flow.
        if courseName == '':
            kwargs["course_detail"] = course.algos.getCourseDetails(courseId,0)
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
        kwargs["isCourseContent"] = 'true'
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
