from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib import auth
from course import models
import provider

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--sessionid', dest='sessionid', required=True)
        parser.add_argument('--chapterid', dest='chapterid', required=True)

    def handle(self, *args, **options):
        sessionid = options['sessionid']
        chapterid = options['chapterid']

        sessionObj = provider.models.Session.objects.filter(id=sessionid)[0]
        chapterObj = models.CourseChapter.objects.filter(id=chapterid)[0]
        chapterObj.sessions.append(sessionid)
        chapterObj.published.append(True)
        chapterObj.save()

        courseObj = models.Course.objects.filter(id=chapterObj.course_id)[0]
        courseObj.sessions = courseObj.sessions + 1
        courseObj.save()
