from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

class Provider(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

def user_directory_path(instance, filename):
    return 'videos/{0}/{1}'.format(instance.provider.id, filename)

class Session(models.Model):
    name = models.CharField(max_length=100)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    uploaded = models.DateTimeField(auto_now_add=True)
    video = models.FileField(upload_to=user_directory_path)
    uploaded = models.DateTimeField(auto_now_add=True)
