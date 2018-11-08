from django.db import models
import provider
import course

# Create your models here.

class Schedule(models.Model):
    provider = models.ForeignKey(provider.models.Provider, on_delete=models.CASCADE)
    chapter = models.ForeignKey(course.models.CourseChapter, on_delete=models.CASCADE)
    start = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(default=60) #minutes
    recurafter = models.IntegerField(default=0) #0 hours => does not recur
