from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.UserDevice)
admin.site.register(models.UserCookieInfo)

