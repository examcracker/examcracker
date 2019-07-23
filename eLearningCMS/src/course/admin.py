from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Course)
admin.site.register(models.CourseChapter)
admin.site.register(models.EnrolledCourse)
admin.site.register(models.SessionStats)