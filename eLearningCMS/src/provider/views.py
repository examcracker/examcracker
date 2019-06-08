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
import profiles
import json
from django.forms.models import model_to_dict
from django.conf import settings
import notification
import student
import os
from examcracker import thread
import cdn
import schedule
from django.contrib.auth import get_user_model
from Crypto.Cipher import AES
from django.contrib.auth import authenticate
import base64

def getDelimiter(subject=False):
    if not subject:
        return course.algos.DELIMITER
    else :
        return course.algos.SUBJECTS_DELIMITER

def getProvider(request):
    providerObj = models.Provider.objects.filter(user_id=request.user.id)
    if providerObj.exists():
      return providerObj[0]
    else:
      return providerObj

def getSessionsBySubjects(providerId,subjects):
    subjectarr = subjects.split(getDelimiter(True))
    sessionObj = models.Session.objects.filter(provider_id=providerId)
    q_objects = Q()
    for sub in subjectarr:
        q_objects.add(Q(tags__icontains=sub), Q.OR)
    sessionObj = sessionObj.filter(q_objects)
    return sessionObj

def getProviderStats(providerId):
    coursesObj = course.models.Course.objects.filter(Q(provider_id=providerId) & Q(published=1))
    sessionObj = models.Session.objects.filter(provider_id=providerId)
    providerStatsInfo = {}
    courses = []
    courses.append(['Courses', 'Students per course'])
    providerStatsInfo['totalCourses'] = '{:,}'.format(len(coursesObj))
    providerStatsInfo['totalSessions'] = '{:,}'.format(len(sessionObj))
    totalStudents = 0
    totalRevenue = 0
    totalViewedMinutes = 0
    for courseObj in coursesObj:
        courseStat = []
        courseStat.append(courseObj.name)
        studentsPerCourse = len(course.models.EnrolledCourse.objects.filter(course_id=courseObj.id))
        totalStudents += studentsPerCourse
        totalRevenue += int(studentsPerCourse*courseObj.cost)
        totalViewedMinutes += int(courseObj.completedseconds/60)
        courseStat.append(studentsPerCourse)
        courses.append(courseStat)
    
    providerStatsInfo['totalStudents'] = '{:,}'.format(totalStudents)
    providerStatsInfo['totalRevenue'] = '{:,}'.format(totalRevenue)
    providerStatsInfo['activeSchedules'] = schedule.views.getActiveSchedules(providerId)
    providerStatsInfo['piechartArray'] = courses
    providerStatsInfo['completedtime'] = str(int(totalViewedMinutes/60)) + " : " + str(int(totalViewedMinutes%60))
    return providerStatsInfo

class showProviderHome(LoginRequiredMixin, generic.TemplateView):
    template_name = 'provider_home.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        notifications = (notification.models.UserNotification.objects.filter(user=request.user.id))
        unseenNotifications = len(notifications.filter(saw=0))
        # set total count of notifications
        kwargs["notificationsCount"] = unseenNotifications
        notifications = notifications.filter(saw=False)
        kwargs["notifications"] = reversed(notifications)

        providerObj = getProvider(request)
        if settings.PROVIDER_APPROVAL_NEEDED and not providerObj.approved:
            kwargs["not_approved"] = True
        else:
            kwargs["statsInfo"] = getProviderStats(providerObj.id)
         
        if schedule.views.isAnyEventLive(request):
            kwargs["live"] = 'on'
        return super().get(request, *args, **kwargs)

class uploadVideo(LoginRequiredMixin, generic.TemplateView):
    template_name = "create_course.html"
    http_method_names = ['post']
    
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

class SessionDurationFetch(thread.CallBackObject):
    def __init__(self, sessionObj):
        super().__init__()
        self.sessionObj = sessionObj

    def execute(self):
        self.sessionObj.duration = cdn.views.getVideoDuration(self.sessionObj.videoKey)

    def terminate(self):
        if self.sessionObj.duration is None:
            return False
        if self.sessionObj.duration == 0:
            return False
        self.sessionObj.ready = True
        self.sessionObj.save()
        return True

def saveCourseContent(request,courseId):
    if 'lcids' not in request.POST:
        return
    courseObj = course.models.Course.objects.filter(id=courseId)[0]
    lcids = request.POST.getlist('lcids')
    chapterNameList = request.POST.getlist('cd[]')
    if len(lcids) > 0:
        i = 0
        subjectChapterCntMap = {}
        chpArr = []
        chpNameIndex = 0
        while i < len(lcids):
            cpid = lcids[i].split('-')
            subject = cpid[1]
            cpSuffix = 1
            chapterName = chapterNameList[chpNameIndex]
            chpNameIndex = chpNameIndex + 1
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
                #chapterObj.name = cpPrefix +' ' +str(cpSuffix) + ': ' + chapterName
            chapterObj.name = chapterName
            #chapterObj.name = cpPrefix +' ' +str(cpSuffix)
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
                    sessionId = filesUploaded[j]

                    try:
                        filesUploaded[j] = int(filesUploaded[j])
                    except:
                        sessionObj = models.Session()
                        sessionObj.provider = getProvider(request)
                        argumentList = sessionId.split('?')
                        sessionObj.videoKey = argumentList[0]
                        sessionObj.name = os.path.splitext(argumentList[1])[0]
                        sessionObj.tags = chapterObj.subject
                        sessionObj.save()
                        sessionId = str(sessionObj.id)

                    sname = request.POST.get('sname['+str(sessionId)+']','')               
                    if sname != '':
                        sessionObj = models.Session.objects.filter(id=sessionId)
                        sessionObj = sessionObj[0]
                        sessionObj.name = sname
                        sessionObj.save()
                    sessionsIdArr.append(sessionId)
                    if course.algos.str2bool(filePublishedArr[j]):
                        publishedArr.append('1')
                    else:
                        publishedArr.append('0')
                    j=j+1
            
            sessionsIdArrStr = getDelimiter().join([str(x) for x in sessionsIdArr])
            publishedArrStr = getDelimiter().join([str(x) for x in publishedArr])
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
        providerObj = getProvider(request)
        if settings.PROVIDER_APPROVAL_NEEDED and not providerObj.approved:
            raise Http404()

        courseId = kwargs.pop('courseId', '')
        if courseId == '':
            courseId = self.request.POST.get("courseId", '')
        courseObj = course.models.Course()
        kwargs["allExams"] = course.models.EXAM_CHOICES
        kwargs["allSubjects"] = course.models.ExamDict

        if courseId != '':
            courseObj = course.models.Course.objects.filter(id=courseId)[0]
            kwargs["editCourse"] = courseObj
            kwargs["editCourseSubjects"] = courseObj.subjects.split(getDelimiter(True))
            kwargs["course_detail"] = course.algos.getCourseDetails(courseId, False)
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
        if 'coursePublic' in self.request.POST:
            courseObj.public = True
        else:
            courseObj.public = False
        

        defaultPic = "course_pics/1.jpg"
        currentPic = ""
        # check if courseObj exists or not
        if courseId != '':
            currentPic = courseObj.picture.name
        else:
            currentPic = defaultPic
            courseObj.picture = currentPic
        # check if new picture received or not
        pictureFileObj = request.FILES.get("course_pic",False)
        pictureFileName = ""
        if  not pictureFileObj:
            pictureFileName = currentPic
        else:
            pictureFileName = pictureFileObj.name
        # check if picture received is different from the current one
        currentPic = os.path.basename(currentPic)
        pictureFileName = os.path.basename(pictureFileName)
        if pictureFileName != currentPic:
            courseObj.picture = pictureFileObj
        
        if (len(subjects) > 0):
            subj = subjects[0].split(':')[1]
            courseObj.subjects = subj
            i=1
            while(i<len(subjects)):
                subj = subjects[i].split(':')[1]
                courseObj.subjects = courseObj.subjects + getDelimiter(True) + subj
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
        courseObjNew.picture = courseObj.picture
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
                courseObjNew.subjects = courseObjNew.subjects + getDelimiter() + courseObj.subjects
            i=i+1
        courseObjNew.save()
        
        childOfParentStr = getDelimiter().join([str(x) for x in childOfParent])
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
        courseObj = course.models.Course.objects.filter(id=courseId)[0]
        courseObj.published = True
        courseObj.save()

        # check if linked course, then return
        if not course.models.LinkCourse.objects.filter(parent_id=courseId).exists():
            # first save course and then publish
            saveCourseContent(request,courseId)
            courseChapterObj = course.models.CourseChapter.objects.filter(course_id=courseId)
            for chapter in courseChapterObj:
                publishedArr = course.algos.strToBoolList(chapter.published)
                lectureCnt = len(publishedArr)

                i = 0
                while i < lectureCnt:
                    publishedArr[i] = '1'
                    i = i + 1

                publishedArrStr =  getDelimiter().join([str(x) for x in publishedArr])
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
            kwargs["courses"] = course.algos.getCourseDetailsForCards(request, courseList)
        return super().get(request, *args, **kwargs)

class ProviderProfile(profiles.views.MyProfile):
    template_name = 'provider_profile.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        notifications = (notification.models.UserNotification.objects.filter(user=request.user.id))
        # set total count of notifications
        kwargs["notificationsCount"] = len(notifications)
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
        kwargs["providerid"] = providerObj.id
        coursesObj = course.models.Course.objects.filter(Q(provider_id=providerObj.id) & Q(published=1))
        courseDictMap = {}
        for courseObj in coursesObj:
            studentsObj = course.models.EnrolledCourse.objects.filter(course_id=courseObj.id)
            if len(studentsObj) == 0:
                continue

            sessionIDList = course.algos.getAllSessionsIdsForCourse(courseObj.id)

            sessionStatsList = []
            for sessionID in sessionIDList:
                sessionStatsObj = course.models.SessionStats.objects.filter(session_id=sessionID)
                if(len(sessionStatsObj) > 0):
                    statsDict = json.loads(sessionStatsObj[0].stats)
                    sessionStatsList.append(statsDict)

            studentList = []
            for studentItem in studentsObj:
                studentInfo = {}
                studentDetails = student.models.Student.objects.filter(id=studentItem.student_id)[0]
                studentInfo['id'] = studentDetails.id
                studentInfo['name'] = course.algos.getUserNameAndPic(studentDetails.user_id)['name']
                studentInfo['enrolled_date'] = studentItem.enrolled

                totalSessionWatched = 0
                totalPlayedCount = 0
                for statsItem in sessionStatsList:
                    studentId = str(studentItem.student_id)
                    if studentId in statsItem:
                        totalSessionWatched += 1
                        totalPlayedCount += statsItem[studentId]

                studentInfo['totalSessions'] = len(sessionIDList)
                studentInfo['totalSessionWatched'] = totalSessionWatched
                studentInfo['totalPlayedCount'] = totalPlayedCount
                studentInfo['viewhours'] = studentItem.viewhours
                studentInfo['completedminutes'] = int(studentItem.completedminutes+0.5)

                if(len(sessionIDList) > 0):
                    studentInfo['CourseCompleted'] = str(int(totalSessionWatched*100/len(sessionIDList))) + '%'
                else:
                    studentInfo['CourseCompleted'] = 'NA'

                studentList.append(studentInfo)

            courseDictMap[courseObj.name] = studentList
        kwargs["course_stats"] = courseDictMap
        return super().get(request, *args, **kwargs)

class liveCapture(showProviderHome):
    template_name = "live_capture.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()

        providerObj = getProvider(request)
        mycourses = course.models.Course.objects.raw('SELECT * from course_course WHERE provider_id = ' + str(providerObj.id) + \
                                                     ' AND id NOT IN (SELECT parent_id from course_linkcourse)')

        courseDict = []
        for c in mycourses:
            courseDetails = course.algos.getCourseDetails(c.id, False)
            courseInfo = {}
            courseInfo['name'] = c.name
            courseInfo['details'] = courseDetails
            courseDict.append(courseInfo)

        kwargs['mycourses'] = courseDict
        return super().get(request, *args, **kwargs)

class addStudents(showProviderHome):
    template_name = "add_students.html"
    http_method_names = ['get', 'post']

    def get(self, request, slug,*args, **kwargs):
        if not request.user.is_staff:
            raise Http404()
        # get courses and chapters of all the courses to enroll students for courses
        # with module level access.
        studentid = int(slug)
        providerObj = getProvider(request)
        courses = course.models.Course.objects.filter(provider_id=providerObj.id)
        courseDict = []
        viewhours = '10'
        for c in courses:
            courseDetails = course.algos.getCourseDetails(c.id, False,False)
            courseInfo = {}
            courseInfo['name'] = c.name
            courseInfo['fullaccess'] = 0
            courseInfo['cid'] = c.id
            
            # do changes in course details map
            if studentid > 0:
                studentObj = student.models.Student.objects.filter(id=studentid)[0]
                kwargs['email'] = course.algos.getUserNameAndPic(studentObj.user_id)['email']
                kwargs['studentname'] = course.algos.getUserNameAndPic(studentObj.user_id)['name']
                enrolledCourseObj = course.models.EnrolledCourse.objects.filter(course_id=c.id,student_id=studentid)
                if enrolledCourseObj:
                    enrolledCourseObj = enrolledCourseObj[0]
                    viewhours = enrolledCourseObj.viewhours
                    courseInfo['viewhours'] = enrolledCourseObj.viewhours
                    if enrolledCourseObj.chapteraccess == '':
                        courseInfo['fullaccess'] = 1
                    else:
                        # extract module level access here for student
                        allowedModules = enrolledCourseObj.chapteraccess.split(',')
                        for sub, subDetails in courseDetails.items():
                            for chapterdetails in subDetails:
                                for chapterid,chapter in chapterdetails.items():
                                    if str(chapterid) in allowedModules:
                                        chapter["access"] = 1
            courseInfo['details'] = courseDetails
            courseDict.append(courseInfo)
        kwargs['mycourses'] = courseDict
        kwargs['viewhours'] = viewhours
            # store 3 info , name, subject and id
        kwargs["courses"] = courses
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()

        #providerObj = getProvider(request)
        emails = self.request.POST.get('email', '')
        studentnames = self.request.POST.get('studentname', '')
        viewhours = self.request.POST.get('viewHours','')
        emailsList = str.split(emails, ',')
        studentnamesList = str.split(studentnames, ',')
        if len(emailsList) == 0:
            return self.get(request, *args, **kwargs)
        
        fullCourses = ''
        if 'course' in self.request.POST:
            fullCourses = self.request.POST.getlist('course')
        modules = [k for k, v in request.POST.items() if k.startswith('modules')]

        if len(emailsList) == 0 :
            return self.get(request, *args, **kwargs)

        # create users and students from emails
        User = get_user_model()
        i = -1
        snameLen = len(studentnamesList)
        fixedEmail = ''
        for email in emailsList:
            fixedEmail = email.strip().lower()
            if not fixedEmail:
                continue
            i = i+1
            userObj = User.objects.filter(email=fixedEmail)
            studentObj = ''
            if not userObj:
                userObj = User(email = fixedEmail)
                userObj.set_password(fixedEmail)
                userObj.name = studentnamesList[i] if i<snameLen else fixedEmail
                userObj.save()
                studentObj = student.models.Student()
                studentObj.user_id = userObj.id
                studentObj.save()
            else:
                userObj = userObj[0]

            if userObj.is_staff or userObj.is_superuser:
                continue
            else:
                studentObj = student.models.Student.objects.filter(user_id=userObj.id)
                if not studentObj:
                    studentObj = student.models.Student()
                    studentObj.user_id = userObj.id
                    studentObj.save()
                else:
                    studentObj = studentObj[0]
            # now enroll courses and modules to this student
            # first enroll full course
            subject = 'Welcome to GyaanHive'
            emailBody = '<p>Dear <span style="color: #ff0000;">' + userObj.name + '</span>,</p>\n\
<p>You have been enrolled for a course or your module access has been changed by <em><strong>' + request.user.name + '</strong></em>.<br />\n\
Login at <strong><a href="https://www.gyaanhive.com">GyaanHive </a></strong>with your email. If you are login for the first time, then give your email in lowercase as password.\n\
The password can be changed from <em>Profile</em> section after login.<br />\n\
Check your <em><strong><a href="https://www.gyaanhive.com/student">Dashboard</a></strong></em> for the courses.<br />\n\
Thanks<br />\n\
Gyaanhive Team</p>'
            courseEnrolledList = []
            enrolledCourses = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id)
            for fc in fullCourses:
                enrolledCourse = course.models.EnrolledCourse.objects.filter(course_id=fc,student_id=studentObj.id)
                viewHours = self.request.POST.get('viewhours'+str(fc))
                courseEnrolledList.append(fc)
                if not enrolledCourse:
                    enrolledCourse = course.models.EnrolledCourse()
                    enrolledCourse.course_id = fc
                    enrolledCourse.student_id = studentObj.id
                else:
                    enrolledCourse = enrolledCourse[0]
                    enrolledCourse.chapteraccess = ''
                #if viewhours != '':
                enrolledCourse.viewhours = viewhours
                enrolledCourse.save()
            for module in modules:
                chapterList = request.POST.getlist(module)
                courseid = module.split('modules')[1]
                courseEnrolledList.append(courseid)
                viewHours = self.request.POST.get('viewhours'+str(courseid))
                enrolledCourse = course.models.EnrolledCourse.objects.filter(course_id=courseid,student_id=studentObj.id)
                if enrolledCourse:
                    enrolledCourse = enrolledCourse[0]
                else:
                    enrolledCourse = course.models.EnrolledCourse()
               
                enrolledCourse.course_id = courseid
                enrolledCourse.student_id = studentObj.id
                #if viewhours != '':
                enrolledCourse.viewhours = viewhours
                modulelist = list(map(int,chapterList))
                enrolledCourse.chapteraccess = ','.join([str(x) for x in modulelist])
                enrolledCourse.save()
                # creare user
            # remove course enrollment here
            coursesToDelete = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id)
            if len(courseEnrolledList) != 0:
                coursesToDelete = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id).exclude(course_id__in=courseEnrolledList)
            if  coursesToDelete:   
                coursesToDelete.delete()

            profiles.signals.sendMail(fixedEmail, subject, emailBody)
        return self.get(request, *args, **kwargs)

AES_KEY = base64.b64decode("iUmAAGnhWZZ75Nq38hG76w==")
AES_IV = base64.b64decode("rgMzT3a413fIAvESuQjt1Q==")

class ProviderCourseDetails(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, email, encpassword, *args, **kwargs):
        decipherObj = AES.new(AES_KEY, AES.MODE_CFB, AES_IV)
        base64pass = base64.b64decode(encpassword.encode())
        decryptedpassword = decipherObj.decrypt(base64pass).decode()

        result = {}

        userObj = authenticate(username=email, password=decryptedpassword)
        if not userObj:
            result['result'] = False
            return JsonResponse(result)

        providerObj = models.Provider.objects.filter(user_id=userObj.id)
        if len(providerObj) == 0:
            result['result'] = False
            return JsonResponse(result)

        providerObj = providerObj[0]

        result['result'] = True
        result['dokey'] = settings.DIGITAL_OCEAN_SPACE_KEY
        result['dosecret'] = settings.DIGITAL_OCEAN_SPACE_KEY_SECRET
        result['drmkeyid'] = settings.DRM_KEY_ID
        result['drmkey'] = settings.DRM_KEY

        result['clientid'] = providerObj.encryptedid
        result['bucketname'] = providerObj.bucketname
        result['courses'] = []

        courses = course.models.Course.objects.filter(provider_id=providerObj.id)
        for c in courses:
            coursedict = {}
            coursedict['id'] = c.id
            coursedict['name'] = c.name
            coursedict['published'] = c.published
            coursedict['created'] = c.created

            chapters = course.models.CourseChapter.objects.filter(course_id=c.id)
            coursedict['chapters'] = []
            for ch in chapters:
                chapterdict = {}
                chapterdict['id'] = ch.id
                chapterdict['name'] = ch.name
                chapterdict['sequence'] = ch.sequence
                chapterdict['subject'] = ch.subject
                chapterdict['published'] = ch.published

                chapterdict['sessions'] = []
                sessionids = course.algos.strToIntList(ch.sessions)
                published = course.algos.strToBoolList(ch.published)

                i = 0
                while i < len(sessionids):
                    s = sessionids[i]
                    sessiondict = {}
                    session = models.Session.objects.filter(id=s)[0]
                    sessiondict['id'] = s
                    sessiondict['name'] = session.name
                    sessiondict['published'] = published[i]
                    sessiondict['uploaded'] = session.uploaded
                    chapterdict['sessions'].append(sessiondict)
                    i = i + 1

                coursedict['chapters'].append(chapterdict)
            result['courses'].append(coursedict)

        return JsonResponse(result)
