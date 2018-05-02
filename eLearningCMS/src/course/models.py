from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import student
import provider

# Create your models here.

EXAM_CHOICES = (
    ('iit','IIT-JEE'),
    ('aieee', 'AIEEE'),
    ('cat','CAT'),
    ('aiims','AIIMs'),
    ('pmt','PMT'),
    ('ias', 'IAS'),
    ('gate', 'GATE'),
    ('gre', 'GRE'),
    ('toefl', 'TOEFL')
)
    
class Course(models.Model):
    name = models.CharField(max_length=100)
    provider = models.ForeignKey(provider.models.Provider, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(default=False)
    exam = models.CharField(choices=EXAM_CHOICES, max_length=10)
    cost = models.IntegerField(default=10000)
    duration = models.IntegerField(default=6)

class EnrolledCourse(models.Model):
    student = models.ForeignKey(student.models.Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    finished = models.BooleanField(default=False)

class CoursePattern(models.Model):
    session = models.ForeignKey(provider.models.Session, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    sequence = models.IntegerField()


