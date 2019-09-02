from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import provider

# Create your models here.

class Student(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class StudentDeviceStats(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    deviceinfo = models.CharField(max_length=1000, blank=True)

class StudentPlayStats(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session = models.ForeignKey(provider.models.Session, on_delete=models.CASCADE)
    lastplayedtime = models.FloatField(default=0)

