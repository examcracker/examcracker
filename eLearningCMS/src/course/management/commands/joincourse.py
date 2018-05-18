from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib import auth
from course import models
import student

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--courseid', dest='courseid', required=True)
        parser.add_argument('--studentid', dest='studentid', required=True)

    def handle(self, *args, **options):
        studentid = options['studentid']
        courseid = options['courseid']

        studentObj = student.models.Student.objects.filter(id=studentid)[0]
        courseObj = models.Course.objects.filter(id=courseid)[0]

        enrolledcourseObj = models.EnrolledCourse()
        enrolledcourseObj.student = studentObj
        enrolledcourseObj.course = courseObj
        enrolledcourseObj.save()
