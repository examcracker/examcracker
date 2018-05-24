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
