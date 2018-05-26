from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib import auth
import django.db.models
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

        maxsequence = models.CourseChapter.objects.filter(course_id=courseid).aggregate(django.db.models.Max('sequence'))['sequence__max']
        if maxsequence is None:
            chapterObj.sequence = 1
        else:
            chapterObj.sequence = maxsequence + 1
        chapterObj.save()
