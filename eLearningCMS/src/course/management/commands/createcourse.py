from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib import auth
from course import models
import provider

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--providerid', dest='providerid', required=True)
        parser.add_argument('--name', dest='name', required=True)
        parser.add_argument('--exam', dest='exam', required=True)
        parser.add_argument('--subjects', dest='subjects', required=True)

    def handle(self, *args, **options):
        providerid = options['providerid']
        name = options['name']
        exam = options['exam']
        subjects = options['subjects']

        providerObj = provider.models.Provider.objects.filter(id=providerid)[0]
        courseObj = models.Course()
        courseObj.provider = providerObj
        courseObj.name = name
        courseObj.exam = exam
        courseObj.subjects = subjects
        courseObj.duration = 6
        courseObj.price = 10000
        courseObj.published = True
        courseObj.save()
