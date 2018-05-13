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
    #basic query to extract all courses
    #query = 'SELECT c.id,c.name, c.created,c.exam, c.duration,c.cost ,authtools_user.name as providerName'
    #query = query + ' from course_course c'
    #query = query + ' INNER JOIN authtools_user ON c.id = authtools_user.id'
    #query = query + ' WHERE (c.published = 1 AND (c.name LIKE \'%'+ searchText + '%\' OR c.exam LIKE \'%'+ searchText +'%\' OR c.id in (select id from authtools_user WHERE name like \'%'+ searchText + '%\')))'
    #courses = models.Course.objects.raw(query)
    #courseList = models.Course.objects.filter(name__icontains=searchText,exam__icontains=searchText)
    providers = User.objects.all()
    providers = providers.filter( Q(name__icontains = searchText))
    courseList = models.Course.objects.filter(Q(published=1)).filter(
    Q(name__icontains=searchText) |
    Q(exam__icontains=searchText) |
    Q( id__in=providers)
    )
    return courseList

# return all published courses
def getPublishedCourses():
    return models.Course.objects.filter(published=1)

#returns exam list
def getExams():
    return models.Course.objects.raw('SELECT * from course_course GROUP BY (exam)')
