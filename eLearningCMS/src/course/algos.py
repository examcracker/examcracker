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
import profiles
import student
import payments
import schedule
from django.forms.models import model_to_dict
from datetime import datetime

DELIMITER = ','
SUBJECTS_DELIMITER = ';'

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

def strToBoolList(array):
  if not array or array == '':
    return []
  out = []
  for ele in array.split(DELIMITER):
    if not str2bool(ele):
      out.append(False)
    else:
      out.append(True)
  return out

def strToIntList(array):
  if not array or array == '':
    return []
  return [int(x) for x in array.split(DELIMITER)]

def intListToStr(array):
  arrayLen = len(array)
  if arrayLen == 0:
    return ''

  out = str(array[0])
  i = 1
  while i < arrayLen:
    out = out + DELIMITER
    out = out + str(array[i])
    i = i + 1

  return out

def boolListToStr(array):
  arrayLen = len(array)
  if arrayLen == 0:
    return ''

  out = str(array[0])
  i = 1
  while i < arrayLen:
    out = out + DELIMITER
    if array[i]:
      out = out + '1'
    else:
      out = out + '0'
    i = i + 1

  return out

# get all sessions for a course (does not work for link courses)
def getAllSessionsIdsForCourse(courseid):
    chapters = models.CourseChapter.objects.filter(course_id=courseid)
    sessions = []

    for c in chapters:
      sessionids = strToIntList(c.sessions)
      published = strToBoolList(c.published)

      i = 0
      while i < len(sessionids):
        if published[i] == True:
          sessions.append(sessionids[i])
        i = i + 1

    return sessions

# get all sessions for a course (does not work for link courses)
def getAllSessionsForCourse(courseid):
    chapters = models.CourseChapter.objects.filter(course_id=courseid)
    sessions = []

    for c in chapters:
      sessionids = strToIntList(c.sessions)
      published = strToBoolList(c.published)

      i = 0
      while i < len(sessionids):
        if published[i] == True:
          sessionObj = provider.models.Session.objects.filter(id=sessionids[i])[0]
          sessions.append(sessionObj)
        i = i + 1

    return sessions

# get all courses for the provider
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
    courseByExams.default_factory = None
    return courseByExams

def parseAndGetSubjectsArr(subjects):
    return subjects.split(SUBJECTS_DELIMITER)

def getCourseDetails(courseid, published=True, getSessions = True,allowedModules = []):
    courseObj = models.LinkCourse.objects.filter(parent_id=courseid)
    courseDetails = {}
    # take map of course name to course details
    if courseObj.exists():
        childCourses = (courseObj[0].child).split(DELIMITER)
        for child in childCourses:
            childCourseObj = models.Course.objects.filter(id=child)[0]
            subjects = parseAndGetSubjectsArr(childCourseObj.subjects)
            i=0
            while(i<len(subjects)):
                courseDetails[subjects[i]] = getCourseDetailsBySubject(child,subjects[i],published, getSessions)
                i=i+1
    else:
        childCourseObj = models.Course.objects.filter(id=courseid)[0]
        subjects = parseAndGetSubjectsArr(childCourseObj.subjects)
        i=0
        while(i<len(subjects)):
            courseDetails[subjects[i]] = getCourseDetailsBySubject(courseid,subjects[i],published, getSessions,allowedModules)
            i=i+1
    return courseDetails

# get course content
def getCourseDetailsBySubject(courseid, subj, onlyPublished = True, getSessions = True,allowedModules=[]):
    courseDetailMap = []
    allowedModulesList = allowedModules
    if len(allowedModules)>0:
      allowedModulesList = list(map(int,allowedModules))
    chapters = models.CourseChapter.objects.filter(course_id=courseid,subject=subj).order_by('sequence')
    cdnSubstr = 'gyaanhive'
    if len(chapters) > 0:
        courseIdNameMap = {}
        for item in chapters:
            if len(allowedModulesList) > 0 and (item.id not in allowedModulesList):
              continue
            courseIdNameMap[item.id] = item.name
            sessions = strToIntList(item.sessions)
            materials = strToIntList(item.material)
            publishedStatus = strToBoolList(item.published)
            chapterDetailMap = {}
            chapterId = item.id
            chapterDetailMap[chapterId] = {}
            # check whether this chapter has any live sessions planned
            scheduleObj = schedule.models.Schedule.objects.filter(chapter_id=item.id)
            if scheduleObj:
                chapterDetailMap[chapterId]["hasLiveSessionsSchedules"] = 1
                
            chapterDetailMap[chapterId]["name"] = item.name
            chapterDetailMap[chapterId]["access"] = 0
            chapterDetailMap[chapterId]["sessions"] = []
            chapterDetailMap[chapterId]["materials"] = []
            chapterDetailMap[chapterId]["duration"] = 0
            chapterDetailMap[chapterId]["hasUnPublishedSessions"] = 0
            i = 0
            while ( (i < len(sessions)) and (getSessions == True) ):
                sess = sessions[i]
                pos = i
                i = i+1
                # Skipping unpublished items
                if not publishedStatus[pos] and onlyPublished :
                    continue
                if not chapterDetailMap[chapterId]["hasUnPublishedSessions"] and not publishedStatus[pos]:
                    chapterDetailMap[chapterId]["hasUnPublishedSessions"] = 1
                
                sessionObj = provider.models.Session.objects.filter(id=sess)[0]
                sessionmaterials= strToIntList(sessionObj.material)
                j = 0
                sessionDetails = {}
                sessionDetails["sessionMaterials"] = []
                while (j < len(sessionmaterials)):
                  mat = sessionmaterials[j]
                  j = j+1
                  materialObj = provider.models.Material.objects.filter(id=mat)
                  if materialObj:
                    materialObj = materialObj[0]
                  else:
                    continue
                  sessionmaterialDetails = {}
                  sessionmaterialDetails["name"] = materialObj.name
                  sessionmaterialDetails["id"] = materialObj.id
                  sessionmaterialDetails["key"] = materialObj.fileKey
                  storageObj = provider.models.Storage.objects.filter(name=materialObj.bucketname)
                  sessionmaterialDetails["bucketname"] = materialObj.bucketname
                  if storageObj:
                    storageObj = storageObj[0]
                    sessionmaterialDetails["bucketname"] = storageObj.pullzone
                  sessionDetails["sessionMaterials"].append(sessionmaterialDetails)
                  sessionmaterialDetails["cdnname"] = 'cdn' + sessionmaterialDetails["bucketname"].replace(cdnSubstr,'')
                sessionDetails["name"] = sessionObj.name
                sessionDetails["video"] = sessionObj.video
                sessionDetails["id"] = sessionObj.id
                sessionDetails["encrypted"] = sessionObj.encrypted
                sessionDetails["published"] = publishedStatus[pos]
                
                chapterDetailMap[chapterId]["sessions"].append(sessionDetails)
                chapterDetailMap[chapterId]["duration"] = chapterDetailMap[chapterId]["duration"] + sessionObj.duration
            i = 0
            while ( (i < len(materials))):
                mat = materials[i]
                pos = i
                i = i+1
                materialDetails = {}
                materialObj = provider.models.Material.objects.filter(id=mat)[0]
                storageObj = provider.models.Storage.objects.filter(name=materialObj.bucketname)
                materialDetails["bucketname"] = materialObj.bucketname
                if storageObj:
                  storageObj = storageObj[0]
                  materialDetails["bucketname"] = storageObj.pullzone
                materialDetails["name"] = materialObj.name
                materialDetails["id"] = materialObj.id
                materialDetails["key"] = materialObj.fileKey
                chapterDetailMap[chapterId]["materials"].append(materialDetails)
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
    courseList = models.Course.objects.filter(published=1,public=1)
    allProviders = getProviders(True)

    if examText is not None:
        courseList = courseList.filter(Q(exam__icontains=examText))
    if providerText is not None:
        userList = allProviders.filter( Q(name__icontains = providerText))
        providerList = provider.models.Provider.objects.filter(Q(user_id__in=userList))
        courseList = courseList.filter(Q(provider_id__in=providerList))
    if searchText == '':
        return courseList
        
    userList = allProviders.filter( Q(name__icontains = searchText))
    providerList = provider.models.Provider.objects.filter(Q(user_id__in=userList))
    courseList = courseList.filter(
    Q(name__icontains=searchText) |
    Q(exam__icontains=searchText) |
    Q(provider_id__in=providerList)
    )
    return courseList

# return all published courses
def getPublishedCourses():
    return models.Course.objects.filter(published=1)

def getCartCourses(studentObj):
    cartCourseId = payments.models.Cart.objects.filter(student_id=studentObj).values('course_id')
    return models.Course.objects.filter(Q(id__in=cartCourseId))

# Returns all exams from our list. Exams list will grow
def getExams():
    return models.EXAM_CHOICES
    #return models.Course.objects.values('exam').annotate(Count('exam')).order_by('exam')

def getProviders(havingPublishedCourses = False):
    User = get_user_model()
    providerObjs = User.objects.filter(is_staff=1)
    if havingPublishedCourses == True:
        providerIds = models.Course.objects.filter(published=1).values('provider_id')
        providerUserIds = provider.models.Provider.objects.filter(Q(id__in = providerIds)).values('user_id')
        providerObjs = providerObjs.filter(Q(id__in = providerUserIds))
    return providerObjs

def getUserNameAndPic(user_id):
    userDetails = {}
    profileObj = profiles.models.Profile.objects.filter(user_id=user_id)[0]
    picture = profileObj.picture
    if picture is not None:
        userDetails['profilePic'] = picture
    try:
        User = get_user_model()
        user = User.objects.filter(id=user_id)[0]
        userDetails['name'] = user.name
        userDetails['email'] = user.email
    except:
        userDetails['name'] = 'Anonymous'

    return userDetails

def getEnrolledStudentsCount(courseId):
    enrolledCount = len(models.EnrolledCourse.objects.filter(course_id=courseId,active=True))
    return enrolledCount

def checkIfStudentEnrolledInCourse(courseId, userId):
    studentObj = student.models.Student.objects.filter(user_id=userId)
    if len(studentObj) > 0:
        studentId = studentObj[0].id
        enrolledStudent = models.EnrolledCourse.objects.filter(course_id=courseId,student_id=studentId,active=True)
        if len(enrolledStudent) > 0:
            return True
    
    return False

def getCourseDetailsForCards(request, courseList):
    allCourses = []
    for item in courseList:
        courseDetails = model_to_dict(item)
        providerObj = provider.models.Provider.objects.filter(id=item.provider_id)[0]
        courseDetails["provider_id"] = item.provider_id
        userDetails = getUserNameAndPic(providerObj.user_id)
        courseDetails["provider_name"] = userDetails['name']
        if 'profilePic' in userDetails: 
            courseDetails["profilePic"] = userDetails['profilePic']
        courseDetails["enrolledCount"] = getEnrolledStudentsCount(item.id)
        if request.user.is_authenticated and request.user.is_staff == False:
            courseDetails["alreadyEnrolled"] = checkIfStudentEnrolledInCourse(item.id, request.user.id)
            if courseDetails["alreadyEnrolled"]:
              studentObj = student.models.Student.objects.filter(user_id=request.user.id)
              studentId = studentObj[0].id
              enrolledStudent = models.EnrolledCourse.objects.filter(course_id=item.id,student_id=studentId,active=True)
              courseDetails["expiry"] = enrolledStudent[0].expiry.strftime('%m/%d/%Y')
        else:
            courseDetails["alreadyEnrolled"] = False
        courseDetails["cost"] = '{:,}'.format(int(courseDetails["cost"]))
        allCourses.append(courseDetails)
    return allCourses

# get courses for a given session
def getCoursesForSession(session_id):
  rawStmt = 'SELECT * FROM course_course WHERE id IN (SELECT course_id FROM course_coursechapter WHERE sessions LIKE \'%,' + str(session_id) + ',%\' OR sessions LIKE \'' + str(session_id) + ',%\' OR sessions LIKE \'%,' + str(session_id) + '\' GROUP BY course_id)'
  flatCourses = models.Course.objects.raw(rawStmt)

  linkCourses = []
  totalCourses = []

  for f in flatCourses:
    totalCourses.append(f.id)
    finalStmt = 'SELECT * from course_course WHERE id IN (SELECT parent_id FROM course_linkcourse WHERE child LIKE \'%,' + str(f.id) + ',%\' OR child LIKE \'' + str(f.id) + ',%\' OR child LIKE \'%,' + str(f.id) + '\')'
    courseObtained = models.Course.objects.raw(finalStmt)

    for c in courseObtained:
      if c.id in linkCourses:
        continue
      linkCourses.append(c.id)

  for l in linkCourses:
    totalCourses.append(l)

  query = Q()
  for course in totalCourses:
    query = query | Q(id=course)

  finalCourses = models.Course.objects.filter(query)
  return finalCourses

def getSubDomain(request):
  host = request.META['HTTP_HOST']
  
  '''
  host = https://www.gyaanhive.com
  With subDomain, it will be 
  host = https://www.subdomain.gyaanhive.com 
  '''
  hostStr = host.split('.')
  if len(hostStr) > 1:
    return hostStr[1]
  return hostStr[0]

def getEnrolledCourseIds(request):
  # first check if subdomain exists in request
  #first get the student from request
  courseids = []
  studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
  sd = getSubDomain(request)
  subDomainObj = provider.models.Subdomain.objects.filter(subdomain = sd)
  enrolledCoursesObj = models.EnrolledCourse.objects.filter(student_id=studentObj.id,active=True)
  todayDate = datetime.now()
  if subDomainObj:
    subDomainObj = subDomainObj[0]
    coursesObj = models.Course.objects.filter(provider_id = subDomainObj.provider_id)
    if coursesObj:
      cids = coursesObj.values('id')
      enrolledCoursesObj = enrolledCoursesObj.filter(course_id__in=cids)

  # Filter those courses whose providers are not approved
  providersNotApproved = provider.models.Provider.objects.filter(approved=False)
  if providersNotApproved:
    pids = providersNotApproved.values('id')
    courseObjsNotApproved = models.Course.objects.filter(provider_id__in=pids)
    if courseObjsNotApproved:
      cids = courseObjsNotApproved.values('id')
      enrolledCoursesObj = enrolledCoursesObj.exclude(course_id__in=cids)
  
  enrolledCoursesObj = enrolledCoursesObj.filter(expiry__gte = todayDate)

  for ec in enrolledCoursesObj:
    courseids.append(ec.course_id)
  
  return courseids

def isCourseAllowed(request,courseid):
  sd = getSubDomain(request)
  subDomainObj = provider.models.Subdomain.objects.filter(subdomain=sd)
  if subDomainObj:
    subDomainObj = subDomainObj[0]
    coursesObj = models.Course.objects.filter(provider_id = subDomainObj.provider_id,id=courseid)
    if coursesObj:
      return True
    else:
      return False
  return True
