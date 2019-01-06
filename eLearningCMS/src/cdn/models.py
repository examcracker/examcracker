from django.db import models
import provider
import course

# Create your models here.

class Logs(models.Model):
    providerencryptedid = models.CharField(max_length=10)
    contents = models.TextField()

