from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib import auth
from course import models
import provider

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--courseid', dest='courseid', required=True)
        parser.add_argument('--name', dest='name', required=True)

    def handle(self, *args, **options):
        courseid = options['courseid']
        name = options['name']

        courseObj = models.Course.objects.filter(id=courseid)[0]
        chapterObj = models.CourseChapter()
        chapterObj.course = courseObj
        chapterObj.name = name
        chapterObj.save()
