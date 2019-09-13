from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import *
import provider
from datetime import date

# Create your models here.

class Student(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class StudentDeviceStats(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    deviceinfo = models.CharField(max_length=1000, blank=True)

class StudentPlayStats(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    sessionname = models.CharField(max_length=1000, blank=True)
    lastplayedtime = models.FloatField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    ipaddress = models.CharField(max_length=200, blank=True)
    deviceinfo = models.CharField(max_length=1000, blank=True)
    otherinfo = models.CharField(max_length=1000, blank=True)

