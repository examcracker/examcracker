from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib import auth
from course import models
import provider

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--sessionid', dest='sessionid', required=True)
        parser.add_argument('--courseid', dest='courseid', required=True)

    def handle(self, *args, **options):
        sessionid = options['sessionid']
        courseid = options['courseid']

        sessionObj = provider.models.Session.objects.filter(id=sessionid)[0]
        courseObj = models.Course.objects.filter(id=courseid)[0]
        coursepatternObj = models.CoursePattern()
        coursepatternObj.course = courseObj
        coursepatternObj.session = sessionObj

        sessions = models.CoursePattern.objects.filter(course_id=courseid)
        maxseq = 0
        for s in sessions:
            if s.sequence > maxseq:
                maxseq = s.sequence

        coursepatternObj.sequence = maxseq + 1
        coursepatternObj.save()
