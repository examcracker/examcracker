from django.views import generic
from course.models import Course
from provider.models import Provider
from course.algos import *
from django.shortcuts import redirect,render
from django.urls import reverse,reverse_lazy
from provider.views import *
import student
import cdn
from course.views import fillCartCourses
from profiles.signals import sendMail
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.contrib.auth import get_user_model
from django.http import HttpResponse

# search by exam , course , provider , substring or exact
class SearchResultsPage(fillCartCourses):
    template_name = "searchResults.html"
    http_method_names = ['get','post']
    
    def get(self, request, *args, **kwargs):
        searchText = request.GET.get('exam','')
        if searchText == '':
            return redirect(reverse_lazy('home'))
        courseList = searchCourseByText(searchText)
        providerObj = getProvider(request)
        if providerObj:
            kwargs["providerId"] = providerObj.id
        kwargs["exams"] = getExams()
        kwargs["providers"] = getProviders(True)
        kwargs["searchResult"] = getCourseDetailsForCards(request, courseList)
        kwargs["searchText"] = searchText
        return super().get(request, *args, **kwargs)

    def post(self, request,*args, **kwargs):
        searchText = request.POST.get('searchText','')
        examText = request.POST.get('examText','')
        providerText = request.POST.get('providerText','')
        # if search string is blank, do nothing. Go to home again
        if searchText == '' and examText == '' and providerText == '':
            return redirect(reverse_lazy('home'))
        courseList = searchCourseByText(searchText,examText,providerText)
        kwargs["exams"] = getExams()
        kwargs["providers"] = getProviders(True)
        kwargs["searchResult"] = getCourseDetailsForCards(request, courseList)
        providerObj = getProvider(request)
        if providerObj:
            kwargs["providerId"] = providerObj.id
        if examText != '':
            searchText = searchText+ ' Exam=' +examText
        if providerText != '':
            searchText = searchText+ ' Provider = ' +providerText
        kwargs["searchText"] = searchText
        return super().get(request, *args, **kwargs)

class listCourses(fillCartCourses):
    template_name = "listOfCourses.html"
    http_method_names = ['get']
    
    def get(self, request, *args, **kwargs):
        courseList = getPublishedCourses()
        courseList = courseList.filter(public=1)
        providerObj = getProvider(request)
        if providerObj:
            kwargs["providerId"] = providerObj.id
        kwargs["allCourses"] = getCourseDetailsForCards(request, courseList)
        return super().get(request, *args, **kwargs)
        
        
# Home page will never post to itself. So removing the post method from Home page
class HomePage(fillCartCourses):
    template_name = "home.html"
    http_method_names = ['get','post']

    def get(self, request, *args, **kwargs):
        examsList = getExams()
        courseList = getPublishedCourses()
        courseList = courseList.filter(public=1)
        providerObj = getProvider(request)
        url = ''
        if request.user.is_authenticated:
            if providerObj:
                kwargs["providerId"] = providerObj.id
                url = 'provider:provider_home'
            elif request.user.is_staff == False:
                url = 'student:student_home'
        else:
            url = 'accounts:login'

        kwargs["exams"] = examsList
        kwargs["allCourses"] = getCourseDetailsForCards(request, courseList)
        allProviders = getProviders(True)
        allProvidersDetails = []
        for provider in allProviders:
            allProvidersDetails.append(getUserNameAndPic(provider.id))
        kwargs["allProviders"] = allProvidersDetails
        resp = super().get(request, *args, **kwargs)
        # set cookie with some default value
        if settings.USER_AUTH_COOKIE not in request.COOKIES.keys():
            resp.set_cookie(settings.USER_AUTH_COOKIE, settings.USER_AUTH_COOKIE_DEFAULT_VALUE,max_age=settings.USER_AUTH_COOKIE_AGE)
        if url != '':
            return redirect(url)
        return resp
        
    
    def post(self, request):
        name = self.request.POST.get('name','')
        email = self.request.POST.get('email','')
        phone = self.request.POST.get('phone','')
        message = self.request.POST.get('message','')
        subject = self.request.POST.get('subject','')
        try:
            emailSub = 'Query from '+ name
            emailBody = 'Hello GyaanHive,\n'
            emailBody = emailBody + 'Name : ' + name + '\n'
            emailBody = emailBody + 'subject : ' + subject + '\n'
            emailBody = emailBody + 'Phone : ' + phone + '\n'
            emailBody = emailBody + 'Email : ' + email + '\n'
            emailBody = emailBody + 'Message : ' + message + '\n'
            sendMail(settings.EMAIL_TO_USER,emailSub,emailBody)
            data = {'result':'success'}
        except:
            data = {'result':'failure'}
        return JsonResponse(data)

class AboutPage(generic.TemplateView):
    template_name = "about.html"

class ContactPage(generic.TemplateView):
    template_name = "contact.html"

class CoursesPage(generic.TemplateView):
    template_name = "courses.html"

class BlogPage(generic.TemplateView):
    template_name = "blog.html"

class PricingPage(generic.TemplateView):
    template_name = "pricing.html"

class DebugPage(generic.TemplateView, LoginRequiredMixin):
    template_name = "debug.html"

    def get(self, request, providerid, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404()

        providerObj = provider.models.Provider.objects.filter(id=providerid)[0]
        fileObj = cdn.models.FileDetails.objects.filter(providerencryptedid=providerObj.encryptedid)
        stateObj = cdn.models.ClientState.objects.filter(providerencryptedid=providerObj.encryptedid)
        logObj = cdn.models.Logs.objects.filter(providerencryptedid=providerObj.encryptedid)
        fileuploadObj = cdn.models.FileUpload.objects.filter(providerencryptedid=providerObj.encryptedid)
        system = provider.models.System.objects.filter(id=providerid)[0].name

        if len(fileObj) > 0:
            kwargs["filedetails"] = fileObj[0]
        if len(stateObj) > 0:
            kwargs["clientstate"] = stateObj[0]
        if len(logObj) > 0:
            kwargs["log"] = logObj[0]
        if len(fileuploadObj) > 0:
            kwargs["fileupload"] = fileuploadObj[0]

        cdn.views.getLogData(request, providerid, system)
        cdn.views.getFileDetails(request, providerid, system)
        cdn.views.getClientState(request, providerid, system)
        kwargs["providerid"] = providerid
        return super().get(request, *args, **kwargs)

    def post(self, request, providerid, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404()

        scheduleid = request.POST.get('schedueid','')
        filename = request.POST.get('filename','')
        system = provider.models.System.objects.filter(id=providerid)[0].name

        cdn.views.sendUploadFileReq(scheduleid, system, filename)
        return self.get(request, providerid, *args, **kwargs)

class fixUsers(generic.TemplateView, LoginRequiredMixin):
    template_name = "debug.html"

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404()
        User = get_user_model()
        userObjs = User.objects.filter(is_staff=0)
        for userObj in userObjs:
            email = userObj.email
            if email.strip() != userObj.email:
                userObj.delete()
                continue
        return super().get(request, *args, **kwargs)


