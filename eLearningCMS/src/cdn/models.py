from django.db import models
import provider
import course

# Create your models here.
class CdnSession(models.Model):
    session = models.ForeignKey(provider.models.Session, on_delete=models.CASCADE)
    ready = models.BooleanField(default=False)
    html = models.CharField(max_length=1000)
    jwvideoid = models.CharField(max_length=10)

class Playlist(models.Model):
    course = models.ForeignKey(course.models.Course, on_delete=models.CASCADE)
    jwid = models.CharField(max_length=10)

class SessionPlaylist(models.Model):
    cdnsession = models.ForeignKey(CdnSession, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
