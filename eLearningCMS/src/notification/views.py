from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from . import models

# Create your views here.

class allNotification(LoginRequiredMixin, generic.TemplateView):
    template_name = 'all.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        notifications = models.UserNotification.objects.filter(user_id=request.user.id)
        kwargs["notificationsCount"] = len(notifications)
        kwargs["notifications"] = reversed(notifications)
        for n in notifications:
            if not n.saw:
                n.saw = True
                n.save()
        return super().get(self, request, *args, **kwargs)
