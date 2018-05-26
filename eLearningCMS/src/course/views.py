from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from collections import OrderedDict
from operator import itemgetter
from django.contrib.auth import get_user_model
from . import models
import course
from course import algos
import provider
import student
import re
import profiles
from collections import defaultdict

# Create your views here.

class courseDetails(generic.TemplateView):
    template_name = 'coursePage.html'
    http_method_names = ['get']

    def get(self, request, id, *args, **kwargs):
        courseid = id

        courseOverviewMap = {}
        courseOverviewMap["id"] = courseid
        courseOverviewMap["myCourse"] = False

        if request.user.is_authenticated:
            if request.user.is_staff == False:
                courseOverviewMap["progress"] = "30%"
                studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
                enrolledCourse = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id).filter(course_id=courseid)
                if len(enrolledCourse) > 0:
                    courseOverviewMap["myCourse"] = True

            elif request.user.is_staff:
                providerObj = provider.models.Provider.objects.filter(user_id=request.user.id)[0]
                courseObj = course.models.Course.objects.filter(id=courseid)[0]
                if courseObj.provider_id == providerObj.id:
                    courseOverviewMap["myCourse"] = True

        courseObj = course.models.Course.objects.filter(id=courseid)[0]
        
        courseOverviewMap["Name"] = courseObj.name
        courseOverviewMap["Description"] = courseObj.description
        courseOverviewMap["Subject"] = courseObj.subjects
        courseOverviewMap["Exam"] = courseObj.exam
        courseOverviewMap["Cost"] = courseObj.cost
        courseOverviewMap["Duration"] = courseObj.duration
        courseOverviewMap["Published"] = courseObj.created

        kwargs["course_overview"] = courseOverviewMap

        courseDetailMap = []
        chapters = course.models.CourseChapter.objects.filter(course_id=courseid).order_by('sequence')

        if len(chapters) > 0:
            courseIdNameMap = {}
            for item in chapters:
                courseIdNameMap[item.id] = item.name
            
                sessions = item.sessions
                publishedStatus = item.published

                chapterDetailMap = {}
                chapterName = item.name
                chapterDetailMap[chapterName] = []

                for sess in sessions:
                    pos = sessions.index(sess)
                    # Skipping unpublished items
                    if not publishedStatus[pos]:
                        continue
                    sessionDetails = {}
                    sessionObj = provider.models.Session.objects.filter(id=sess)[0]
                    sessionDetails["name"] = sessionObj.name 
                    sessionDetails["video"] = sessionObj.video 
                    sessionDetails["id"] = sessionObj.id
                    chapterDetailMap[chapterName].append(sessionDetails)

                courseDetailMap.append(chapterDetailMap)

        kwargs["course_detail"] = courseDetailMap
        return super().get(request, id, *args, **kwargs)

class playSession(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']
    template_name = 'playSession.html'

    def get(self, request, chapterid, sessionid, *args, **kwargs):
        courseChapterObj = course.models.CourseChapter.objects.filter(id=chapterid)[0]

        # check whether the session is in that course
        if sessionid not in courseChapterObj.sessions:
            kwargs["wrong_content"] = True
            return super().get(request, chapterid, sessionid, *args, **kwargs)

        # if user is student, allow only if enrolled for the course and session is published
        if request.user.is_staff == False:
            index = courseChapterObj.sessions.index(sessionid)
            if courseChapterObj.published[index] == False:
                kwargs["not_published"] = True
                return super().get(request, chapterid, sessionid, *args, **kwargs)

            studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
            enrolledCourse = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id).filter(course_id=courseChapterObj.course_id)
            if len(enrolledCourse) == 0:
                kwargs["not_enrolled"] = True
                return super().get(request, chapterid, sessionid, *args, **kwargs)

            enrolledCourseObj = enrolledCourse[0]
            if sessionid not in enrolledCourseObj.sessions:
                enrolledCourseObj.sessions.append(sessionid)
                enrolledCourseObj.save()

        # if user is provider, allow only if he is the course owner and session is added to the course (draft or published)
        if request.user.is_staff:
            providerObj = provider.models.Provider.objects.filter(user_id=request.user.id)[0]
            courseObj = course.models.Course.objects.filter(id=courseChapterObj.course_id)[0]
            if courseObj.provider_id != providerObj.id:
                kwargs["wrong_provider"] = True
                return super().get(request, chapterid, sessionid, *args, **kwargs)

        return super().get(request, chapterid, sessionid, *args, **kwargs)
