from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from django.urls import reverse
from collections import OrderedDict
from operator import itemgetter
from django.http import QueryDict
from collections import defaultdict
from django.http import Http404
from math import ceil
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from . import models
import course
from course import algos
import cdn
import provider
import student
import re
import profiles
import payments


User = get_user_model()

# Create your views here.
class fillCartCourses(generic.TemplateView):
    http_method_names = ['get']
    
    def get(self, request, *args, **kwargs):
        studentObj = student.views.getStudent(request)
        if studentObj:
            cartCoursesList = algos.getCartCourses(studentObj)
            allCourses = []
            tcost = 0
            for item in cartCoursesList:
                courseDetails = model_to_dict(item)
                providerObj = provider.models.Provider.objects.filter(id=item.provider_id)[0]
                userDetails = algos.getUserNameAndPic(providerObj.user_id)
                courseDetails["provider_name"] = userDetails['name']
                tcost = tcost + int(courseDetails["cost"])
                allCourses.append(courseDetails)
            kwargs["tcost"] = tcost
            kwargs["cartCourses"] = allCourses
        return super().get(request, *args, **kwargs)

def getCourseReview(reviewSummary, userReviewList, courseid):
    reviewObj = course.models.CourseReview.objects.filter(course_id=courseid)
    reviewSummary['star_count'] = range(1, 6)
    reviewSummary['totalReviews'] = len(reviewObj)
    reviewSummary['1'] = 0
    reviewSummary['2'] = 0
    reviewSummary['3'] = 0
    reviewSummary['4'] = 0
    reviewSummary['5'] = 0
    totalRating = 0
    for review in reviewObj:
        if review.rating > 0 and review.rating <= 5:
            reviewSummary[str(review.rating)] += 1
            totalRating += review.rating
            userDetails = algos.getUserNameAndPic(review.student_id)
           
            userDetails['review'] = review.review
            userDetails['rating'] = int(review.rating)
            userDetails['reviewedTime'] = review.reviewed
            
            userReviewList.append(userDetails)

    if totalRating > 0:       
        reviewSummary['averageRating'] = (int(totalRating*10.0/len(reviewObj)))/10.0
        reviewSummary['1Avg'] = str((int(reviewSummary['1']*100.0/len(reviewObj)))) + "%"
        reviewSummary['2Avg'] = str((int(reviewSummary['2']*100.0/len(reviewObj)))) + "%"
        reviewSummary['3Avg'] = str((int(reviewSummary['3']*100.0/len(reviewObj)))) + "%"
        reviewSummary['4Avg'] = str((int(reviewSummary['4']*100.0/len(reviewObj)))) + "%"
        reviewSummary['5Avg'] = str((int(reviewSummary['5']*100.0/len(reviewObj)))) + "%"


class courseDetails(fillCartCourses):
    template_name = 'coursePage.html'
    http_method_names = ['get', 'post']

    def get(self, request, id, *args, **kwargs):
        courseid = id
        courseObj = course.models.Course.objects.filter(id=courseid)

        if len(courseObj) == 0:
            raise Http404()

        courseObj = courseObj[0]

        if courseObj.published == False:
            kwargs["not_published"] = True
            raise Http404()

        courseOverviewMap = {}
        courseOverviewMap["id"] = courseid
        courseOverviewMap["myCourse"] = False

        #################Get review details########################

        reviewSummary = {}
        userReviewList = []

        getCourseReview(reviewSummary, userReviewList, courseid)

        kwargs['userReviewList'] = userReviewList

        ##########################################################

        courseDetailMap = algos.getCourseDetails(id)
        kwargs["course_detail"] = courseDetailMap

        if request.user.is_authenticated:
            if request.user.is_staff == False:
                studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
                enrolledCourse = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id).filter(course_id=courseid)
                if len(enrolledCourse) > 0:
                    courseOverviewMap["myCourse"] = True
                    reviewSummary["enrolledCourse"] = True

                    # calculate duration completed
                    durationCompleted = 0
                    totalDuration = 0
                    enrolledCourseObj = enrolledCourse[0]

                    if enrolledCourseObj.sessions != '':
                        sessionsPlayed = course.algos.strToIntList(enrolledCourseObj.sessions)
                        for s in sessionsPlayed:
                            sessionObj = provider.models.Session.objects.filter(id=s)[0]
                            durationCompleted = durationCompleted + sessionObj.duration

                    for subj in courseDetailMap:
                        chapters = courseDetailMap[subj]
                        for chapDetails in chapters:
                            for chapId in chapDetails:
                                chapDetail = chapDetails[chapId]
                                totalDuration = totalDuration + chapDetail["duration"]

                    if totalDuration > 0:
                        courseOverviewMap["progress"] = str(ceil(durationCompleted*100/totalDuration)) + '%'
                    else:
                        courseOverviewMap["progress"] = "0%"

                addedCourse = payments.models.Cart.objects.filter(course_id=courseid).filter(student_id=studentObj.id)
                if len(addedCourse) > 0:
                    courseOverviewMap["addedCourse"] = True
            else:
                providerObj = provider.models.Provider.objects.filter(user_id=request.user.id)[0]
                if courseObj.provider_id == providerObj.id:
                    courseOverviewMap["myCourse"] = True

        courseOverviewMap["Name"] = courseObj.name
        courseOverviewMap["Description"] = courseObj.description
        courseOverviewMap["Subject"] = courseObj.subjects
        courseOverviewMap["Exam"] = courseObj.exam
        courseOverviewMap["Cost"] = courseObj.cost
        courseOverviewMap["Duration"] = courseObj.duration
        courseOverviewMap["Published"] = courseObj.created
        courseOverviewMap["picture"] = courseObj.picture

        kwargs["course_overview"] = courseOverviewMap
        kwargs['reviewSummary'] = reviewSummary

        return super().get(request, id, *args, **kwargs)

    def post(self, request, id, *args, **kwargs):
        courseid = id
        studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
        courseObj = course.models.Course.objects.filter(id=courseid)[0]
        cart = payments.models.Cart()
        cart.student = studentObj
        cart.course = courseObj

        if "join" in request.POST:
            cart.checkout = True
            cart.save()
            query_dictionary = QueryDict('', mutable=True)
            query_dictionary.update({'id': courseid})
            url = '{base_url}?{querystring}'.format(base_url=reverse("payments:process"),
                                                querystring=query_dictionary.urlencode())
            return redirect(url)

class playSession(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']
    template_name = 'playSession.html'

    def get(self, request, chapterid, sessionid, *args, **kwargs):
        courseChapterObj = course.models.CourseChapter.objects.filter(id=chapterid)

        if len(courseChapterObj) == 0:
            raise Http404()

        courseChapterObj = courseChapterObj[0]
        sessions = str.split(courseChapterObj.sessions, ",")

        # check whether the session is in that course
        if str(sessionid) not in sessions:
            raise Http404()

        # if user is student, allow only if enrolled for the course and session is published
        if request.user.is_staff == False:
            index = sessions.index(str(sessionid))
            if courseChapterObj.published[index] == False:
                raise Http404()

            studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
            enrolledCourse = course.models.EnrolledCourse.objects.filter(student_id=studentObj.id).filter(course_id=courseChapterObj.course_id)
            if len(enrolledCourse) == 0:
                raise Http404()

            coursesWithSession = algos.getCoursesForSession(sessionid)

            for c in coursesWithSession:
                enrolledCourseObj = models.EnrolledCourse.objects.filter(student_id=studentObj.id).filter(course_id=c.id)
                if len(enrolledCourseObj) > 0:
                    enrolledCourseObj = enrolledCourseObj[0]
                    sessionsPlayed = algos.strToIntList(enrolledCourseObj.sessions)
                    if sessionid in sessionsPlayed:
                        continue

                    sessionsPlayed.append(sessionid)
                    enrolledCourseObj.sessions = algos.intListToStr(sessionsPlayed)
                    enrolledCourseObj.save()

        # if user is provider, allow only if he is the course owner and session is added to the course (draft or published)
        if request.user.is_staff:
            providerObj = provider.models.Provider.objects.filter(user_id=request.user.id)[0]
            courseObj = course.models.Course.objects.filter(id=courseChapterObj.course_id)[0]
            if courseObj.provider_id != providerObj.id:
                kwargs["wrong_provider"] = True
                raise Http404()

        sessionObj = provider.models.Session.objects.filter(id=sessionid)[0]
        '''
        if sessionObj.duration == 0:
            raise Http404()
        '''

        kwargs["coursedetails"] = algos.getCourseDetails(courseChapterObj.course_id)
        kwargs["videoid"] = cdn.views.getCdnSessionForSession(sessionid).jwvideoid

        return super().get(request, chapterid, sessionid, *args, **kwargs)

class addReview(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['post']

    def post(self, request, id, *args, **kwargs):
        courseid = id
        studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
        courseObj = course.models.Course.objects.filter(id=courseid)[0]

        CourseReviewObj = models.CourseReview()
        CourseReviewObj.student = studentObj
        CourseReviewObj.course = courseObj
        CourseReviewObj.review = request.POST.get('review')
        CourseReviewObj.rating = int(request.POST.get('stars'))
        CourseReviewObj.save()

        url = "course:coursePage"
        return redirect(url,courseid)
