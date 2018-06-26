from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from . import models
from django.http import JsonResponse
from django.db.models import Q
from django.http import Http404
from . import forms
import course
import datetime
import pdb
import profiles
import json

def getProvider(request):
    providerObj = models.Provider.objects.filter(user_id=request.user.id)
    if providerObj.exists():
      return providerObj[0]
    else:
      return providerObj

def getSessionsBySubjects(providerId,subjects):
    subjectarr = subjects.split(';')
    sessionObj = models.Session.objects.filter(provider_id=providerId)
    q_objects = Q()
    for sub in subjectarr:
        q_objects.add(Q(tags__icontains=sub), Q.OR)
    sessionObj = sessionObj.filter(q_objects)
    return sessionObj

class showProviderHome(LoginRequiredMixin, generic.TemplateView):
    template_name = 'provider_home.html'

class uploadVideo(LoginRequiredMixin, generic.TemplateView):
    template_name = "create_course.html"
    http_method_names = ['get', 'post']
    
    def post(self, request):
        providerObj = getProvider(request)
        videoForm = forms.uploadFilesForm(self.request.POST,self.request.FILES)
        courseid = self.request.POST.get('coid','')
        subject = ''
        #pdb.set_trace()
        if courseid != "":
            courseObj = course.models.Course.objects.filter(id=int(courseid))[0]
            subject = courseObj.subjects
        if videoForm.is_valid():
            sessionObj = videoForm.save(commit=False)
            sessionObj.provider = getProvider(request)
            sessionObj.name = sessionObj.video.name
            if subject != '':
                sessionObj.tags = subject
            sessionObj.save()
            videoForm.save()
            data = {'is_valid': True, 'videoId': sessionObj.id, 'videoName': sessionObj.name}
            return JsonResponse(data)
        else:
            data = {'is_valid': False}
            return JsonResponse(data)


class coursePageGetter(LoginRequiredMixin, generic.TemplateView):
    template_name = 'create_course.html'
    http_method_names = ['get','post']

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()
        profileObj = profiles.models.Profile.objects.filter(user_id=request.user.id)[0]
        if not profileObj.email_verified:
            kwargs["email_pending"] = True
        courseId = kwargs.pop('courseId', '')
        if courseId == '':
            courseId = self.request.POST.get("courseId", '')
        providerObj = getProvider(request)
        if courseId == '':
            courseId = request.POST.get("courseId", '')
        courseObj = course.models.Course()
        kwargs["allExams"] = course.models.EXAM_CHOICES
        kwargs["allSubjects"] = course.models.ExamDict
        allProviderChildCourses = course.algos.getAllChildCoursesbyExamsFromProvider(providerObj.id)
        kwargs["allChildCoursesByMe"] = allProviderChildCourses
        kwargs["allChildCoursesCount"] = len(allProviderChildCourses)
        if courseId != '':
            courseObj = course.models.Course.objects.filter(id=courseId)[0]
            kwargs["editCourse"] = courseObj
            kwargs["editCourseSubjects"] = courseObj.subjects.split(';')
            kwargs["course_detail"] = course.algos.getLinkedCourseDetails(courseId, 0)
            kwargs["sessionsBySubjects"] = getSessionsBySubjects(providerObj.id, courseObj.subjects)
        return super().get(request, *args, **kwargs)

class createCourse(coursePageGetter):
    template_name = 'create_course.html'
    http_method_names = ['get','post']

    def post(self, request,*args, **kwargs):
        if not request.user.is_staff:
            raise Http404()

        profileObj = profiles.models.Profile.objects.filter(user_id=request.user.id)[0]
        if not profileObj.email_verified:
            kwargs["email_pending"] = True
        
        isCourseContent = request.POST.get('isCourseContent','')
        courseId = request.POST.get('courseId','')
        courseObj = course.models.Course()
        providerObj = getProvider(request)

        if courseId != '':
            #return super().get(request, *args, **kwargs)
            kwargs["courseId"] = courseId
            courseObj = course.models.Course.objects.filter(id=courseId)[0]

        # check if course content flow
        if isCourseContent != '':
            if 'lcids' not in request.POST:
                return super().get(request, *args, **kwargs)
            lcids = request.POST.getlist('lcids')
            if len(lcids) > 0:
                cpPrefix = 'Chapter '              
                i = 0
                while i < len(lcids):
                    cpid = lcids[i]
                    chapterObj = course.models.CourseChapter.objects.filter(id=cpid,course_id=courseId)
                    if chapterObj.exists():
                        chapterObj = chapterObj[0]
                    else:
                        chapterObj = course.models.CourseChapter()
                        chapterObj.course = courseObj
                    chapterObj.name = cpPrefix + str(i+1)
                    chapterObj.sequence = i+1
                    # first get and save files into provider_session db
                    sessionsIdArr = []
                    publishedArr = []
                    # get session ids here
                    lcVar = 'lec['+str(lcids[i])+'][]'
                    lecPubVar = 'lecPub['+str(lcids[i])+'][]'
                    if lcVar in request.POST:
                        filesUploaded = request.POST.getlist(lcVar)
                        filePublishedArr = request.POST.getlist(lecPubVar)
                        j=0
                        while j<len(filesUploaded):
                            sessionsIdArr.append(filesUploaded[j])
                            publishedArr.append(filePublishedArr[j])
                            j=j+1
                    chapterObj.sessions=sessionsIdArr
                    chapterObj.published=publishedArr
                    chapterObj.save()
                    i=i+1
            return super().get(request, *args, **kwargs)
        # try to segregate the procs for course description creation and 
        # course content creation
        courseName = request.POST.get('courseName','')
        # check if Edit course flow.
        if courseName == '':
            return super().get(request, *args, **kwargs)

        # no need to validate, validation already done in html form
        courseObj.name = courseName
        courseObj.description=request.POST.get('courseDescription','')
        courseObj.exam=request.POST.get("courseExam",'')
        courseObj.provider=getProvider(request)
        courseObj.cost=request.POST.get("courseCost",'')
        courseObj.duration=request.POST.get("courseDuration",'')
        subjects = request.POST.getlist("courseSubject")
        subj = subjects[0].split(':')[1]
        courseObj.subjects = subj
        i=1
        while(i<len(subjects)):
            subj = subjects[i].split(':')[1]
            courseObj.subjects = courseObj.subjects+";"+subj
            i=i+1
        courseObj.save()
        kwargs["isCourseContent"] = 'true'
        kwargs["courseId"] = courseObj.id
        return super().get(request, *args, **kwargs)

class createFromCourses(coursePageGetter):
    template_name = "create_course.html"
    http_method_names = ['get','post']

    def post(self, request,*args, **kwargs):
        providerObj = getProvider(request)
        courseObjNew = course.models.Course()        
        courseObjNew.provider=providerObj
        courseObjNew.save()

        if 'courseIDS[]' not in self.request.POST:
            return render(request, self.template_name)
        cIDS = self.request.POST.getlist('courseIDS[]')
        courseObj = course.models.Course.objects.filter(id=cIDS[0])[0]
        linkCourse = course.models.LinkCourse()
        linkCourse.parent = courseObjNew
        linkCourse.child.append(courseObj.id)
        courseObjNew.name = courseObj.name
        courseObjNew.description = courseObj.description
        courseObjNew.cost = courseObj.cost
        courseObjNew.duration = courseObj.duration
        courseObjNew.exam = courseObj.exam
        courseObjNew.subjects = courseObj.subjects
        i=1
        while(i<len(cIDS)):
            cid = cIDS[i]
            linkCourse.child.append(cid)
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
        linkCourse.save()
        # add sessions from all courses into new course
        newCid = courseObjNew.id
        '''i=0
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
            i=i+1'''
        kwargs["courseId"] = newCid
        return super().get(request, *args, **kwargs)

class publishCourse(coursePageGetter):
    #template_name = "create_course.html"
    http_method_names = ['get','post']

    def post(self, request,*args, **kwargs):
        providerObj = getProvider(request)
        courseId = self.request.POST.get('courseId','')
        courseChapterObj = course.models.CourseChapter.objects.filter(course_id=courseId)
        if courseId != '':
            courseObj = course.models.Course.objects.filter(id=courseId)[0]
            courseObj.published=True
            courseObj.save()
            # check if linked course, then return
            if not course.models.LinkCourse.objects.filter(parent_id=courseId).exists():
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
            kwargs["courseId"] = courseId
            return super().get(request, *args, **kwargs)
        else:
            data = {'is_valid': False}
            return super().get(request, *args, **kwargs)

class editCourse(coursePageGetter):
    template_name = 'create_course.html'
    http_method_names = ['get','post']

    def get(self, request, id, *args, **kwargs):
        #pdb.set_trace()
        if not request.user.is_staff:
            raise Http404()
        courseid = id
        courseObj = course.models.Course.objects.filter(id=courseid)
        if len(courseObj) == 0:
            raise Http404()
        courseObj = courseObj[0]
        # use this in template to populate the fields
        kwargs["edit_course"] = courseObj
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

class showStudentProfile(LoginRequiredMixin, generic.TemplateView):
    template_name = 'my_profile.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        profileObj = profiles.models.Profile.objects.filter(user_id=request.user.id)[0]
        kwargs["userDetails"] = profileObj
        kwargs["authUserDetails"] = request.user
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        userObj = request.user
        profileObj = profiles.models.Profile.objects.filter(user_id=request.user.id)[0]
        picture = self.request.FILES.get("profile_pic")
        if picture is not None:
            profileObj.picture = picture

        profileObj.bio = self.request.POST.get("bio")
        profileObj.address = self.request.POST.get("address")
        profileObj.city = self.request.POST.get("city")
        profileObj.country = self.request.POST.get("country")
        profileObj.phone = self.request.POST.get("mobile")

        userObj.name = self.request.POST.get("name")
        userObj.email = self.request.POST.get("email")

        userObj.save()
        profileObj.save()
        return redirect("provider:my_profile")

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


