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
from django.forms.models import model_to_dict
from course import algos
import notification
import student

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
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        notifications = reversed(notification.models.UserNotification.objects.filter(user=request.user.id, saw=False))
        kwargs["notifications"] = notifications
        return super().get(request, *args, **kwargs)

class uploadVideo(LoginRequiredMixin, generic.TemplateView):
    template_name = "create_course.html"
    http_method_names = ['get', 'post']
    
    def post(self, request):
        providerObj = getProvider(request)
        videoForm = forms.uploadFilesForm(self.request.POST,self.request.FILES)
        courseid = self.request.POST.get('coid','')
        subject = ''

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

def saveCourseContent(request,courseId):
    if 'lcids' not in request.POST:
        return
    courseObj = course.models.Course.objects.filter(id=courseId)[0]
    lcids = request.POST.getlist('lcids')
    if len(lcids) > 0:
        cpPrefix = 'Chapter '              
        i = 0
        subjectChapterCntMap = {}
        #pdb.set_trace()
        chpArr = []
        while i < len(lcids):
            cpid = lcids[i].split('-')
            subject = cpid[1]
            cpSuffix = 1
            if subject not in subjectChapterCntMap:
                subjectChapterCntMap[subject] = 1
                cpSuffix = 1
            else:
                subjectChapterCntMap[subject] = subjectChapterCntMap[subject] + 1
                cpSuffix = subjectChapterCntMap[subject]
            chapterObj = course.models.CourseChapter.objects.filter(id=cpid[0],course_id=courseId,subject=subject)
            if chapterObj.exists():
                chapterObj = chapterObj[0]
            else:
                chapterObj = course.models.CourseChapter()
                chapterObj.course = courseObj
            chapterObj.name = cpPrefix +' ' +str(cpSuffix)
            chapterObj.sequence = i+1
            chapterObj.subject = subject

            # first get and save files into provider_session db
            sessionsIdArr = []
            publishedArr = []

            # get session ids here
            lcVar = 'lec['+str(cpid[0])+'][]'
            lecPubVar = 'lecPub['+str(cpid[0])+'][]'
            if lcVar in request.POST:
                filesUploaded = request.POST.getlist(lcVar)
                filePublishedArr = request.POST.getlist(lecPubVar)
                j=0
                while j < len(filesUploaded):
                    sessionsIdArr.append(filesUploaded[j])
                    if course.algos.str2bool(filePublishedArr[j]):
                        publishedArr.append('1')
                    else:
                        publishedArr.append('0')
                    j=j+1
            
            sessionsIdArrStr =  ','.join([str(x) for x in sessionsIdArr])
            publishedArrStr =  ','.join([str(x) for x in publishedArr])
            chapterObj.sessions = sessionsIdArrStr
            chapterObj.published = publishedArrStr
            chapterObj.save()
            chpArr.append(chapterObj.id)

            i=i+1
        fullCourse = course.models.CourseChapter.objects.filter(course_id=courseId).exclude(id__in=chpArr)
        fullCourse.delete()
    return

class coursePageBase(showProviderHome):
    template_name = 'create_course.html'
    http_method_names = ['get']

    def get(self,request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()
        courseId = kwargs.pop('courseId', '')
        if courseId == '':
            courseId = self.request.POST.get("courseId", '')
        providerObj = getProvider(request)
        if courseId == '':
            courseId = request.POST.get("courseId", '')
        courseObj = course.models.Course()
        kwargs["allExams"] = course.models.EXAM_CHOICES
        kwargs["allSubjects"] = course.models.ExamDict
        if courseId != '':
            courseObj = course.models.Course.objects.filter(id=courseId)[0]
            kwargs["editCourse"] = courseObj
            kwargs["editCourseSubjects"] = courseObj.subjects.split(';')
            kwargs["course_detail"] = course.algos.getCourseDetails(courseId, 0)
            courseObj = course.models.Course.objects.filter(id=courseId)[0]
            linkCourseObj = course.models.LinkCourse.objects.filter(parent_id=courseId)
            if linkCourseObj.exists():
                kwargs["editContentDisable"] = True
            else:
                kwargs["editContentDisable"] = False
            kwargs["sessionsBySubjects"] = getSessionsBySubjects(providerObj.id, courseObj.subjects)
        else :
            allProviderChildCourses = course.algos.getAllChildCoursesbyExamsFromProvider(providerObj.id)
            kwargs["allChildCoursesByMe"] = allProviderChildCourses
            kwargs["allChildCoursesCount"] = len(allProviderChildCourses)
        return super().get(request, *args, **kwargs)

class createCourse(coursePageBase):
    http_method_names = ['get','post']

    def post(self, request,*args, **kwargs):
        if not request.user.is_staff:
            raise Http404()
        profileObj = profiles.models.Profile.objects.filter(user_id=request.user.id)[0]
        isCourseContent = request.POST.get('isCourseContent','')
        courseId = request.POST.get('courseId','')
        courseObj = course.models.Course()

        if courseId != '':
            kwargs["courseId"] = courseId
            courseObj = course.models.Course.objects.filter(id=courseId)[0]

        # check if course content flow
        if isCourseContent != '':
            saveCourseContent(request,courseId)
            kwargs["isCourseContent"] = True
            return super().get(request, *args, **kwargs)

        # no need to validate, validation already done in html form
        courseObj.name = request.POST.get('courseName','')
        courseObj.description=request.POST.get('courseDescription','')
        courseObj.exam=request.POST.get("courseExam",'')
        courseObj.provider=getProvider(request)
        courseObj.cost=request.POST.get("courseCost",'')
        courseObj.duration=request.POST.get("courseDuration",'')
        subjects = request.POST.getlist("courseSubject")
        if (len(subjects) > 0):
            subj = subjects[0].split(':')[1]
            courseObj.subjects = subj
            i=1
            while(i<len(subjects)):
                subj = subjects[i].split(':')[1]
                courseObj.subjects = courseObj.subjects+";"+subj
                i=i+1
        courseObj.save()
        kwargs["isCourseContent"] = True
        kwargs["courseId"] = courseObj.id
        return super().get(request, *args, **kwargs)

class createFromCourses(coursePageBase):
    http_method_names = ['post']

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
        childOfParent = []
        childOfParent.append(courseObj.id)
        #linkCourse.child.append(courseObj.id)
        courseObjNew.name = courseObj.name
        courseObjNew.description = courseObj.description
        courseObjNew.cost = courseObj.cost
        courseObjNew.duration = courseObj.duration
        courseObjNew.exam = courseObj.exam
        courseObjNew.subjects = courseObj.subjects
        i=1
        while(i<len(cIDS)):
            cid = cIDS[i]
            childOfParent.append(cid)
            #linkCourse.child.append(cid)
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
        childOfParentStr = ','.join([str(x) for x in childOfParent])
        linkCourse.child = childOfParentStr
        linkCourse.save()
        # add sessions from all courses into new course
        newCid = courseObjNew.id
        kwargs["courseId"] = newCid
        return super().get(request, *args, **kwargs)

class publishCourse(coursePageBase):
    http_method_names = ['post']

    def post(self, request,*args, **kwargs):
        providerObj = getProvider(request)
        courseId = self.request.POST.get('courseId','')
        # first save course and then publish
        #pdb.set_trace()
        saveCourseContent(request,courseId)
        #pdb.set_trace()
        courseChapterObj = course.models.CourseChapter.objects.filter(course_id=courseId)
        courseObj = course.models.Course.objects.filter(id=courseId)[0]
        courseObj.published = True
        courseObj.save()
        # check if linked course, then return
        if not course.models.LinkCourse.objects.filter(parent_id=courseId).exists():
            for chapter in courseChapterObj:
                #pdb.set_trace()
                publishedArr = course.algos.strToBoolList(chapter.sessions)
                lectureCnt = len(publishedArr)

                i = 0
                while i < lectureCnt:
                    publishedArr[i] = '1'
                    i = i + 1

                publishedArrStr =  ','.join([str(x) for x in publishedArr])
                chapter.published = publishedArrStr
                chapter.save()
        kwargs["courseId"] = courseId

        enrolledCourse = course.models.EnrolledCourse.objects.filter(course_id=courseId)
        for c in enrolledCourse:
            studentUserObj = student.models.Student.objects.filter(id=c.student_id)[0]
            notification.models.notify(studentUserObj.user_id, notification.models.COURSE_PUBLISHED, notification.models.INFO, courseObj.name)

        return super().get(request, *args, **kwargs)

class editCourse(coursePageBase):

    http_method_names = ['get']

    def get(self, request, id, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()
        courseid = id
        courseObj = course.models.Course.objects.filter(id=courseid)
        if len(courseObj) == 0:
            raise Http404()
        kwargs["courseId"] = courseid
        kwargs["isCourseContent"] = True
        return super().get(request, *args, **kwargs)

class viewSessions(LoginRequiredMixin, generic.TemplateView):
    template_name = "view_videos.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        providerObj = getProvider(request)
        sessionList = models.Session.objects.filter(provider_id=providerObj.id)
        kwargs["sessions"] = sessionList
        return super().get(request, *args, **kwargs)

class viewCourses(showProviderHome):
    template_name = "view_courses.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        providerObj = getProvider(request)
        if providerObj:
            kwargs["providerId"] = providerObj.id
            courseList = course.models.Course.objects.filter(provider_id=providerObj.id)
            allCourses = []
            for item in courseList:
                courseDetails = model_to_dict(item)
                courseDetails["provider_id"] = providerObj.id
                userDetails = algos.getUserNameAndPic(providerObj.id)
                courseDetails["provider_name"] = userDetails['name']
                if 'profilePic' in userDetails: 
                    courseDetails["profilePic"] = userDetails['profilePic']
                courseDetails["enrolledCount"] = algos.getEnrolledStudentsCount(item.id)
                courseDetails["cost"] = '{:,}'.format(int(courseDetails["cost"]))
                allCourses.append(courseDetails)

            kwargs["courses"] = allCourses
        return super().get(request, *args, **kwargs)

class ProviderProfile(profiles.views.MyProfile):
    template_name = 'provider_profile.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
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


class myStudents(showProviderHome):
    template_name = "my_students.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()

        providerObj = getProvider(request)
        coursesObj = course.models.Course.objects.filter(provider_id=providerObj.id)
        courses = []
        courses.append(['Courses', 'Students per course'])
        for courseObj in coursesObj:
            courseStat = []
            courseStat.append(courseObj.name)
            studentsPerCourse = len(course.models.EnrolledCourse.objects.filter(course_id=courseObj.id))
            courseStat.append(studentsPerCourse)
            courses.append(courseStat)
        courseDictMap = {}
        courseDictArray = []
        courseDictMap["myCourse"] = True
        courseDict = {}
        courseDict['name'] = "Students distribution per course"
        courseDict['chartTitleeee'] = ""
        courseDict['piechartArray'] = courses
        courseDict['progressbarShow'] = False
        courseDictArray.append(courseDict)
        courseDictMap["outertemplateArray"] = courseDictArray
        kwargs["course_overview"] = courseDictMap
        return super().get(request, *args, **kwargs)
