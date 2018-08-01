from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# Create your models here.

class UserDevice(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    device = models.CharField(max_length=1000, blank=True)
    key = models.CharField(max_length=32, blank=True)
    time = models.IntegerField(default=0)
    challenge = models.CharField(max_length=32, blank=True)
    candidate = models.CharField(max_length=300, blank=True)


