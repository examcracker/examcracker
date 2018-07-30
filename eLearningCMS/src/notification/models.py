from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

# Create your models here.

INFO = 1
WARNING = 2
ERROR = 3

COURSE_PUBLISHED = 100
DEVICE_ADDED = 101
EMAIL_NOT_VERIFIED = 102

class UserNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    args = models.CharField(max_length=100, blank=True)
    level = models.IntegerField(default=0)

def notify(userid, notificationType, level, *args):
    notificationObj = UserNotification(user=User.objects.filter(id=userid)[0])
    notificationObj.notification = notificationType
    notificationObj.level = level

    for a in args:
        if not notificationObj.args:
            notificationObj.args = a
        else:
            notificationObj.args = notificationObj.args + ":" + a
    notificationObj.save()

