from django.db import models
import provider
import course

# Create your models here.
class cdnSession(models.Model):
    session = models.ForeignKey(provider.models.Session, on_delete= models.CASCADE)
    ready = models.BooleanField(default=False)
    html = models.CharField(max_length=1000)
    jwvideoid = models.CharField(max_length=10)

class Playlist(models.Model):
    course = models.ForeignKey(course.models.Course, on_delete=models.CASCADE)
    jwid = models.CharField(max_length=10)
