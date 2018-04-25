from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
import uuid
from django.db import models
from django.conf import settings


class BaseProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                primary_key=True)
    slug = models.UUIDField(default=uuid.uuid4, blank=True, editable=False)
    # Add more user profile fields here. Make sure they are nullable
    # or with default values
    picture = models.ImageField('Profile picture',
                                upload_to='profile_pics/%Y-%m-%d/',
                                null=True,
                                blank=True)
    bio = models.CharField("Short Bio", max_length=200, blank=True, null=True)
    email_verified = models.BooleanField("Email verified", default=False)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class Profile(BaseProfile):
    def __str__(self):
        return "{}'s profile". format(self.user)

class Student(models.Model):
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=30)
    phone = models.CharField(max_length=10)

class Provider(models.Model):
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=30)
    phone = models.CharField(max_length=10)

class Course(models.Model):
    name = models.CharField(max_length=50)
    provider_id = models.ForeignKey(Provider, on_delete=models.CASCADE)

class EnrolledCourse(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    finished = models.BooleanField(default=False)

class Session(models.Model):
    url = models.CharField(max_length=100)
    provider_id = models.ForeignKey(Provider, on_delete=models.CASCADE)

class CoursePattern(models.Model):
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    sequence = models.IntegerField()
