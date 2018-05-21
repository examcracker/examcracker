from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib import auth
from provider import models

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--providerid', dest='providerid', required=True)
        parser.add_argument('--path', dest='path', required=True)
        parser.add_argument('--tags', dest='tags', required=True)

    def handle(self, *args, **options):
        providerid = options['providerid']
        path = options['path']
        tags = options['tags']

        providerObj = models.Provider.objects.filter(id=providerid)[0]
        sessionObj = models.Session()
        sessionObj.provider = providerObj
        sessionObj.name = sessionObj.video = path
        sessionObj.tags = tags
        sessionObj.save()
