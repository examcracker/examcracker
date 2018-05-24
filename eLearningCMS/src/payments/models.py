from django.db import models
import course
import student

# Create your models here.

class Cart(models.Model):
    course = models.ForeignKey(course.models.Course, on_delete=models.CASCADE)
    student = models.ForeignKey(student.models.Student, on_delete=models.CASCADE)
    checkout = models.BooleanField(default=False)
