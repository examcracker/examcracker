from django.views import generic
from course.models import Course
from provider.models import Provider
from course.algos import *
from django.shortcuts import redirect,render
from django.urls import reverse,reverse_lazy
from provider.views import *
import student
from course.views import fillCartCourses

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
        providerObj = getProvider(request)
        if providerObj:
            kwargs["providerId"] = providerObj.id
        kwargs["allCourses"] = getCourseDetailsForCards(request, courseList)
        return super().get(request, *args, **kwargs)
        
        
# Home page will never post to itself. So removing the post method from Home page
class HomePage(fillCartCourses):
    template_name = "home.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        examsList = getExams()
        courseList = getPublishedCourses()
        providerObj = getProvider(request)
        if providerObj:
            kwargs["providerId"] = providerObj.id
        kwargs["exams"] = examsList
        kwargs["allCourses"] = getCourseDetailsForCards(request, courseList)
        allProviders = getProviders(True)
        allProvidersDetails = []
        for provider in allProviders:
            allProvidersDetails.append(getUserNameAndPic(provider.id))

        kwargs["allProviders"] = allProvidersDetails

        return super().get(request, *args, **kwargs)

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
