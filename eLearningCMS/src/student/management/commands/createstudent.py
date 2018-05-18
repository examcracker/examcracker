from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib import auth
from student import models

User = get_user_model()

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--email', dest='email', required=True)
        parser.add_argument('--name', dest='name', required=True)

    def handle(self, *args, **options):
        email = options['email']
        name = options['name']
        userObj = User()
        userObj.email = email
        userObj.name = name
        userObj.save()

        studentObj = models.Student()
        studentObj.user = userObj
        studentObj.save()
