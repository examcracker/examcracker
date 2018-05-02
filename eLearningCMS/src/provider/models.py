from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# Create your models here.

class Provider(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class Session(models.Model):
    url = models.CharField(max_length=100)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)

