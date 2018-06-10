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

import json
# http://gsl.mit.edu/media/programs/india-summer-2012/materials/json_django.pdf

def getProvider(request):
    providerObj = models.Provider.objects.filter(user_id=request.user.id)
    if providerObj.exists():
      return providerObj[0]
    else:
      return providerObj

class showProviderHome(LoginRequiredMixin, generic.TemplateView):
    template_name = 'provider_home.html'

class uploadVideo(LoginRequiredMixin, generic.TemplateView):
    template_name = "create_course.html"
    http_method_names = ['get', 'post']
    
    def post(self, request):
        providerObj = getProvider(request)
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

class createFromCourses(LoginRequiredMixin, generic.TemplateView):
    template_name = "create_course.html"
    http_method_names = ['get', 'post']

    def post(self, request):
        providerObj = getProvider(request)
        #return super().get(request)
        #pdb.set_trace()
        courseObjNew = course.models.Course()        
        courseObjNew.provider=providerObj
        if 'courseIDS[]' not in self.request.POST:
            return render(request, self.template_name)
        cIDS = self.request.POST.getlist('courseIDS[]')
        #return super().get(request)
        courseObj = course.models.Course.objects.filter(id=cIDS[0])[0]
        courseObjNew.name = courseObj.name
        courseObjNew.description = courseObj.description
        courseObjNew.cost = courseObj.cost
        courseObjNew.duration = courseObj.duration
        courseObjNew.exam = courseObj.exam
        courseObjNew.subjects = courseObj.subjects
        i=1
        while(i<len(cIDS)):
            cid = cIDS[i]
            courseObj = course.models.Course.objects.filter(id=cid)[0]
            courseObjNew.name = courseObjNew.name + " and " + courseObj.name
            courseObjNew.description = courseObjNew.description + " and " + courseObj.description
            courseObjNew.cost = courseObjNew.cost + courseObj.cost
            courseObjNew.duration = courseObjNew.duration + courseObj.duration
            courseObjNew.exam = courseObj.exam
            if courseObj.subjects not in courseObjNew.subjects :
                courseObjNew.subjects = courseObjNew.subjects + ";" + courseObj.subjects
            i=i+1
        courseObjNew.save()
        # add sessions from all courses into new course
        newCid = courseObjNew.id
        i=0
        chCnt = 1
        while (i<len(cIDS)) :
            cid = cIDS[i]
            courseChapterObj = course.models.CourseChapter.objects.filter(course_id=cid).order_by('sequence')
            for chapter in courseChapterObj:
                courseChapterNewObj = course.models.CourseChapter()
                courseChapterNewObj.course_id = newCid
                courseChapterNewObj.name = 'Chapter '+str(chCnt)
                courseChapterNewObj.sequence = chCnt
                for session in chapter.sessions:
                    courseChapterNewObj.sessions.append(session)
                    courseChapterNewObj.published.append(False)
                courseChapterNewObj.save()
                chCnt = chCnt+1
            i=i+1
        return render(request, self.template_name, {"editCourse" : courseObjNew,"editCourseSubjects" :courseObj.subjects.split(';'), "allExams" : course.models.EXAM_CHOICES , "allSubjects" : course.models.ExamDict, "course_detail" : course.algos.getCourseDetails(newCid,0)})

class publishCourse(LoginRequiredMixin, generic.TemplateView):
    template_name = "create_course.html"
    http_method_names = ['get', 'post']

    def post(self, request):
        providerObj = getProvider(request)
        courseId = self.request.POST.get('courseId','')
        courseChapterObj = course.models.CourseChapter.objects.filter(course_id=courseId)
        if courseId != '':
            courseObj = course.models.Course.objects.filter(id=courseId)[0]
            for chapter in courseChapterObj:
                lectureCnt = len(chapter.sessions)
                i = 0
                publishedArr = []
                while i < len(chapter.sessions):
                    publishedArr.append(True)
                    i=i+1
                chapter.published = publishedArr
                chapter.save()
            data = {'is_valid': True, 'courseId': courseId}
            courseObj.published=True
            courseObj.save()
            return render(request, self.template_name, {"editCourse" : courseObj, "editCourseSubjects" :courseObj.subjects.split(';'),  "allExams" : course.models.EXAM_CHOICES , "allSubjects" : course.models.ExamDict, "course_detail" : course.algos.getCourseDetails(courseId,0)})
        else:
            data = {'is_valid': False}
            return render(request, self.template_name)

class createCourse(LoginRequiredMixin, generic.TemplateView):
    template_name = 'create_course.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        providerObj = getProvider(request)
        courseId = request.POST.get("courseId",'')
        courseObj = course.models.Course()
        kwargs["allExams"] = course.models.EXAM_CHOICES
        kwargs["allSubjects"] = course.models.ExamDict
        allProviderCourses = course.algos.getAllCoursesbyExamsFromProvider(providerObj.id)
        kwargs["allCoursesByMe"] = allProviderCourses
        kwargs["allCoursesCount"] = course.models.Course.objects.filter(provider_id=providerObj.id).count()
        #pdb.set_trace()
        if courseId != '':
            courseObj = course.models.Course.objects.filter(id=courseId)[0]
            kwargs["editCourse"] = courseObj
            kwargs["editCourseSubjects"] = courseObj.subjects.split(';')
            kwargs["course_detail"] = course.algos.getCourseDetails(courseId,0)
        return super().get(request, *args, **kwargs)

    def post(self, request,*args, **kwargs):
        #return super().get(request, *args, **kwargs)
        isCourseContent = request.POST.get('isCourseContent','')
        courseId = request.POST.get('courseId','')
        courseObj = course.models.Course()
        if courseId != '':
            kwargs["courseId"] = courseId
            courseObj = course.models.Course.objects.filter(id=courseId)[0]
            kwargs["editCourse"] = courseObj
            kwargs["editCourseSubjects"] = courseObj.subjects.split(';')
            kwargs["course_detail"] = course.algos.getCourseDetails(courseId,0)
        kwargs["allExams"] = course.models.EXAM_CHOICES
        kwargs["allSubjects"] = course.models.ExamDict
        providerObj = getProvider(request)

        # check if course content flow
        if isCourseContent != '':
            #return super().get(request, *args, **kwargs)
            # auto writing chapter names
            #pdb.set_trace()
            course.models.CourseChapter.objects.filter(course_id=courseId).delete()
            kwargs["course_detail"] = course.algos.getCourseDetails(courseId,0)
            if 'lcids' not in request.POST:
                return super().get(request, *args, **kwargs)
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
                    lcVar = 'lec['+str(lcids[i-1])+'][]'
                    lecPubVar = 'lecPub['+str(lcids[i-1])+'][]'
                    
                    if lcVar in request.POST:
                        filesUploaded = request.POST.getlist(lcVar)
                        filePublishedArr = request.POST.getlist(lecPubVar)
                        j=0
                        #pdb.set_trace()
                        while j<len(filesUploaded):
                            sessionsIdArr.append(filesUploaded[j])
                            publishedArr.append(filePublishedArr[j])
                            j=j+1
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
        subjects = request.POST.getlist("courseSubject")
        #pdb.set_trace()
        subj = subjects[0].split(':')[1]
        courseObj.subjects = subj
        i=1
        while(i<len(subjects)):
            subj = subjects[i].split(':')[1]
            courseObj.subjects = courseObj.subjects+";"+subj
            i=i+1
        courseObj.save()
        kwargs["editCourse"] = courseObj
        kwargs["editCourseSubjects"] = courseObj.subjects.split(';')
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
