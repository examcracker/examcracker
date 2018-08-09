from django.db import models
import provider

# Create your models here.
class cdnSession(models.Model):
    session = models.ForeignKey(provider.models.Session, on_delete= models.CASCADE)
    ready = models.BooleanField(default=False)
    html = models.CharField(max_length=1000)
    vimeo = models.IntegerField(default=0)

