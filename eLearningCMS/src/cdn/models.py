from django.db import models
import provider
import course

# Create your models here.
class CdnSession(models.Model):
    session = models.ForeignKey(provider.models.Session, on_delete=models.CASCADE)
    ready = models.BooleanField(default=False)
    jwvideoid = models.CharField(max_length=10)
