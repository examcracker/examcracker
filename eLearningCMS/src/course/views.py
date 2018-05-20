from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from collections import OrderedDict
from operator import itemgetter
from django.contrib.auth import get_user_model
from . import models
import course
from course import algos
import provider
import re
import profiles

# Create your views here.

class courseDetails(generic.TemplateView):
    template_name = 'coursePage.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
