from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from . import models
from . import forms
import course

class showStudentHome(LoginRequiredMixin, generic.TemplateView):
    template_name = 'student_home.html'
