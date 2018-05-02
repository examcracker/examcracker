from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import student
import provider

# Create your models here.
    
class Course(models.Model):
    name = models.CharField(max_length=50)
    provider = models.ForeignKey(provider.models.Provider, on_delete=models.CASCADE)

class EnrolledCourse(models.Model):
    student = models.ForeignKey(student.models.Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    finished = models.BooleanField(default=False)

class CoursePattern(models.Model):
    session = models.ForeignKey(provider.models.Session, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    sequence = models.IntegerField()


