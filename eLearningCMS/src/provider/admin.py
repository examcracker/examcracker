from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Session)
admin.site.register(models.Provider)
admin.site.register(models.System)
admin.site.register(models.Plan)
admin.site.register(models.DrmSession)
admin.site.register(models.Subdomain)
admin.site.register(models.Storage)
admin.site.register(models.Material)
admin.site.register(models.Bandwidth)
