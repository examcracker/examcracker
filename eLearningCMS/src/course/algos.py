from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from . import models
import re
from collections import OrderedDict
from operator import itemgetter
from django.db.models import Q
from django.contrib.auth import get_user_model

# returns the 'count' courses which have maximum students
def mostEnrolledCourses(count):
    return models.Course.objects.raw('SELECT * FROM course_course WHERE id IN (SELECT course_id FROM course_enrolledcourse GROUP BY course_id ORDER BY COUNT(course_id) DESC LIMIT ' + str(count) + ')')

# return all courses which have 'searchtext' delimited by ' ,'
def searchCourses(searchtext, provider = None, exam = None):
    tokens = re.split(' |,', searchtext)
    coursesDict = {}

    query = 'SELECT * from course_course WHERE published = 1'
    if provider is not None:
        query = query + ' AND provider_id = ' + str(provider)
    if exam is not None:
        query = query + ' AND exam = \'' + exam + '\''

    for text in tokens:
            if text == '':
                continue
            courses = models.Course.objects.raw(query + ' AND name LIKE \'%' + text + '%\'')

            for c in courses:
                if c in coursesDict.keys():
                    coursesDict[c] = coursesDict[c] + 1
                else:
                    coursesDict[c] = 1

    courseList = OrderedDict(sorted(coursesDict.items(), key = itemgetter(1)))
    return courseList

# Assuming search text to be either substring of course , provider or exam
def searchCourseByText(searchText):
    User = get_user_model()
    providers = User.objects.all().filter( Q(name__icontains = searchText))
    courseList = models.Course.objects.filter(Q(published=1)).filter(
    Q(name__icontains=searchText) |
    Q(exam__icontains=searchText) |
    Q( id__in=providers)
    )
    return courseList.values('name','created','exam','cost','duration','provider__user__name')

# return all published courses
def getPublishedCourses():
    return models.Course.objects.filter(published=1)

#returns exam list
def getExams():
    return
    #return models.Course.objects.raw('SELECT * from course_course GROUP BY (exam)')
