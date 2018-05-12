from django.views import generic
from course.models import Course
from provider.models import Provider
from course.algos import *

class HomePage(generic.TemplateView):
    template_name = "home.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        examsList = getExams()
        courseList = getPublishedCourses()
        kwargs["exams"] = examsList
        kwargs["allCourses"] = courseList
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
