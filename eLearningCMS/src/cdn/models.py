from django.db import models
import provider
import course

# Create your models here.

class Logs(models.Model):
    providerencryptedid = models.CharField(max_length=10)
    contents = models.TextField()

class ClientState(models.Model):
    providerencryptedid = models.CharField(max_length=10)
    when = models.DateTimeField(auto_now=True)

class FileDetails(models.Model):
    providerencryptedid = models.CharField(max_length=10)
    details = models.CharField(max_length=100)
    when = models.DateTimeField(auto_now=True)

