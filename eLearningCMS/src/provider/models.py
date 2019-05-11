from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.forms import forms
from django.core.files.storage import FileSystemStorage
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from Crypto.Cipher import AES
import json
import os
import base64

aes_key = base64.b64decode("iUmAAGnhWZZ75Nq38hG76w==")
aes_iv = base64.b64decode("rgMzT3a413fIAvESuQjt1Q==")

class Provider(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    encryptedid = models.CharField(default='', max_length=30)
    bucketname = models.CharField(default='', max_length=100)

    def save(self):
        super().save()
        cipher = AES.new(aes_key, AES.MODE_CFB, aes_iv)
        self.encryptedid = base64.b64encode(cipher.encrypt(str(self.id).encode())).decode()
        super().save()

def user_directory_path(instance, filename):
    return 'sessions/{0}/{1}'.format(instance.provider.id, filename)

class Session(models.Model):
    name = models.CharField(max_length=100)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    uploaded = models.DateTimeField(auto_now_add=True)
    video = models.FileField(upload_to=user_directory_path)
    ready = models.BooleanField(default=False)
    videoKey = models.CharField(max_length=20, default='')
    tags = models.CharField(max_length=100)
    duration = models.IntegerField(default=0) #in secs
    encrypted = models.BooleanField(default=False)

class DrmSession(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    keyid = models.CharField(max_length=50, default='')
    key = models.CharField(max_length=50, default='')

class System(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    name = models.CharField(default='', max_length=100)

class Plan(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    cost = models.IntegerField(default=0)
    bandwidth = models.IntegerField(default=0) # per month or year
    space = models.IntegerField(default=0) # per year


