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
        chapter = course.models.CourseChapter.objects.filter(course_id=courseid)

        if len(chapter) > 0:
            for item in chapter:
                chapterDetailMap = {}
                chapterDetailMap[item.chapter] = []
                patterns = course.models.CoursePattern.objects.filter(chapter_id=item.id)
                for pattern in patterns:
                    session= provider.models.Session.objects.filter(id=pattern.session_id)
                    for sess in session:
                        sessionDetails= {}
                        sessionDetails["name"] = sess.name 
                        sessionDetails["video"] = sess.video 
                
                        chapterDetailMap[item.chapter].append(sessionDetails)

                courseDetailMap.append(chapterDetailMap) 


        kwargs["course_detail"] = courseDetailMap

        return super().get(request, id, *args, **kwargs)

class playSession(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']
    template_name = 'playSession.html'

    def get(self, request, courseid, sessionid, *args, **kwargs):
        coursePattern = course.models.CoursePattern.objects.filter(course_id=courseid).filter(session_id=sessionid)
        # check whether the session is in that course
        if len(coursePattern) == 0:
            kwargs["wrong_content"] = True
            return super().get(request, courseid, sessionid, *args, **kwargs)

        # if user is student, allow only if enrolled for the course and session is published
        if request.user.is_staff == False:
            if coursePattern[0].published == False:
                kwargs["not_published"] = True
                return super().get(request, courseid, sessionid, *args, **kwargs)

            studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
            enrolledCourse = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id).filter(course_id=courseid)
            if len(enrolledCourse) == 0:
                kwargs["not_enrolled"] = True
                return super().get(request, courseid, sessionid, *args, **kwargs)

            enrolledCourseObj = enrolledCourse[0]
            alreadyViewed = False
            for s in enrolledCourseObj.sessions:
                if s == sessionid:
                    alreadViewed = True
                    break
            if alreadyViewed == False:
                enrolledCourseObj.sessions.append(sessionid)
                enrolledCourseObj.save()

        # if user is provider, allow only if he is the course owner and session is added to the course (draft or published)
        if request.user.is_staff:
            providerObj = provider.models.Provider.objects.filter(user_id=request.user.id)[0]
            courseObj = course.models.Course.objects.filter(id=courseid)[0]
            if courseObj.provider_id != providerObj.id:
                kwargs["wrong_provider"] = True
                return super().get(request, courseid, sessionid, *args, **kwargs)

        return super().get(request, courseid, sessionid, *args, **kwargs)
