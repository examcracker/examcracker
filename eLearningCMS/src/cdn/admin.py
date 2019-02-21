from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.Logs)
admin.site.register(models.ClientState)
admin.site.register(models.FileDetails)
