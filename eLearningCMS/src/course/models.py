from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
import student
import provider

# Create your models here.

EXAM_CHOICES = (
    ('IIT-JEE','IIT-JEE'),
    ('AIEEE', 'AIEEE'),
    ('CAT','CAT'),
    ('AIIMS','AIIMS'),
    ('PMT','PMT'),
    ('IAS', 'IAS'),
    ('GATE', 'GATE'),
    ('GRE', 'GRE'),
    ('TOEFL', 'TOEFL')
)
    
class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    provider = models.ForeignKey(provider.models.Provider, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    exam = models.CharField(choices=EXAM_CHOICES, max_length=10)
    cost = models.IntegerField(default=10000)
    duration = models.IntegerField(default=6)
    subjects = models.CharField(max_length=100)
    published = models.BooleanField(default=False)
    sessions = models.IntegerField(default=0)

class EnrolledCourse(models.Model):
    student = models.ForeignKey(student.models.Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled = models.DateTimeField(auto_now_add=True)
    sessions = ArrayField(models.IntegerField(), default=list, blank=True)

class CourseChapter(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    sequence = models.IntegerField(default=0)
    sessions = ArrayField(models.IntegerField(), default=list, blank=True)
    published = ArrayField(models.BooleanField(), default=list, blank=True)
