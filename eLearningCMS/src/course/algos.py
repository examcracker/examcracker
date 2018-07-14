from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from . import models
import re
from collections import OrderedDict
from operator import itemgetter
from django.db.models import Q
from django.db.models import Count
from django.contrib.auth import get_user_model
from collections import defaultdict
import provider
import pdb

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

#get all courses for the provider
def getAllChildCoursesbyExamsFromProvider(pId):
    courseByExams = defaultdict(list)
    examsByProviders= models.Course.objects.filter(provider_id=pId)
    examsByProviders = examsByProviders.values('exam').annotate(cnt = Count('exam')).filter(cnt__gte=2)
    if not examsByProviders.exists():
        return courseByExams
    courseObj = models.Course.objects.filter(provider_id=pId).filter(exam__in=examsByProviders.values('exam'))
    courseObj = courseObj.exclude(id__in=models.LinkCourse.objects.all().values('parent'))
    for course in courseObj:
        courseDetails = {}
        courseDetails["name"] = course.name
        courseDetails["id"]=course.id
        courseByExams[course.exam].append(courseDetails)
    #pdb.set_trace()
    courseByExams.default_factory = None
    return courseByExams

def parseAndGetSubjectsArr(subjects):
    return subjects.split(';')


def getCourseDetails(courseid,published=1):
    courseObj = models.LinkCourse.objects.filter(parent_id=courseid)
    #pdb.set_trace()
    courseDetails = {}
    # take map of course name to course details
    if courseObj.exists():
        childCourses = courseObj[0].child
        for child in childCourses:
            childCourseObj = models.Course.objects.filter(id=child)[0]
            subjects = parseAndGetSubjectsArr(childCourseObj.subjects)
            i=0
            while(i<len(subjects)):
                courseDetails[subjects[i]] = getCourseDetailsBySubject(child,subjects[i],published)
                i=i+1
    else:
        childCourseObj = models.Course.objects.filter(id=courseid)[0]
        subjects = parseAndGetSubjectsArr(childCourseObj.subjects)
        i=0
        while(i<len(subjects)):
            courseDetails[subjects[i]] = getCourseDetailsBySubject(courseid,subjects[i],published)
            i=i+1
    return courseDetails

# get course content
def getCourseDetailsBySubject(courseid, subj,onlyPublished = 1):
    courseDetailMap = []
    chapters = models.CourseChapter.objects.filter(course_id=courseid,subject=subj).order_by('sequence')

    if len(chapters) > 0:
        courseIdNameMap = {}

        for item in chapters:
            courseIdNameMap[item.id] = item.name
            
            sessionsStrArr = item.sessions.split(',')
            sessions = []
            if len(sessionsStrArr) > 0 and sessionsStrArr[0]!= '':
                sessions = [int(x) for x in sessionsStrArr]
            #sessions = item.sessions

            publishedStatusStrArr = item.published.split(',')
            publishedStatus = []
            if len(publishedStatusStrArr) > 0 and publishedStatusStrArr[0] != '':
                publishedStatus = [str2bool(x) for x in publishedStatusStrArr]
            #publishedStatus = item.published

            chapterDetailMap = {}

            chapterId = item.id
            chapterDetailMap[chapterId] = {}
            chapterDetailMap[chapterId]["name"] = item.name
            chapterDetailMap[chapterId]["sessions"] = []
            chapterDetailMap[chapterId]["duration"] = 0

            for sess in sessions:
                pos = sessions.index(sess)
                # Skipping unpublished items
                if not publishedStatus[pos] and onlyPublished == 1 :
                    continue
                sessionDetails = {}
                sessionObj = provider.models.Session.objects.filter(id=sess)[0]
                sessionDetails["name"] = sessionObj.name
                sessionDetails["video"] = sessionObj.video
                sessionDetails["id"] = sessionObj.id
                sessionDetails["published"] = publishedStatus[pos]
                chapterDetailMap[chapterId]["sessions"].append(sessionDetails)
                chapterDetailMap[chapterId]["duration"] = chapterDetailMap[chapterId]["duration"] + sessionObj.duration

            courseDetailMap.append(chapterDetailMap)
    return courseDetailMap

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
def searchCourseByText(searchText,examText=None,providerText=None):
    User = get_user_model()
    
    # get all courses and providers, then apply filter queries on them
    courseList = models.Course.objects.filter(published=1)
    allProviders = getProviders()

    if examText is not None:
        courseList = courseList.filter(Q(exam__icontains=examText))
    if providerText is not None:
        userList = allProviders.filter( Q(name__icontains = providerText))
        providerList = provider.models.Provider.objects.filter(Q(user_id__in=userList))
        courseList = courseList.filter(Q(provider_id__in=providerList))
    if searchText == '':
        return courseList.values('id','name','created','exam','cost','duration','provider__user__name')
        
    userList = allProviders.filter( Q(name__icontains = searchText))
    providerList = provider.models.Provider.objects.filter(Q(user_id__in=userList))
    courseList = courseList.filter(
    Q(name__icontains=searchText) |
    Q(exam__icontains=searchText) |
    Q(provider_id__in=providerList)
    )
    return courseList.values('id','name','created','exam','cost','duration','provider__user__name')

# return all published courses
def getPublishedCourses():
    return models.Course.objects.filter(published=1)

# Returns all exams from our list. Exams list will grow
def getExams():
    return models.EXAM_CHOICES
    #return models.Course.objects.values('exam').annotate(Count('exam')).order_by('exam')

def getProviders():
    User = get_user_model()
    return User.objects.filter(is_staff=1)
