from django.views.generic.edit import CreateView
from django.views import generic
from django.http import JsonResponse

class index(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request):
        data = {'is_valid': True}
        return JsonResponse(data)
