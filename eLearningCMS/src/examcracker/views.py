from django.views import generic
from course.models import Course
from provider.models import Provider
from course.algos import *
from django.shortcuts import redirect,render
from django.urls import reverse,reverse_lazy

class HomePage(generic.TemplateView):
    template_name = "home.html"
    http_method_names = ['get','post']

    def get(self, request, *args, **kwargs):
        examsList = getExams()
        courseList = getPublishedCourses()
        kwargs["exams"] = examsList
        kwargs["allCourses"] = courseList
        return super().get(request, *args, **kwargs)

    def post(self, request):
        searchText = request.POST['searchText']
        # if search string is blank, do nothing. Go to home again
        if searchText == '':
            return redirect(reverse_lazy('home'))
        courseList = searchCourseByText(searchText)
        return render(request, self.template_name, {"searchResult" : courseList,"searchText" : searchText} )

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
