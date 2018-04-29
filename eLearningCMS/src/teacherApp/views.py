from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

class showTeacher(LoginRequiredMixin, generic.TemplateView):
    template_name = 'teacherPage.html'
