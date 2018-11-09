from django.shortcuts import render
import course
from provider.views import showProviderHome, getProvider
# Create your views here.

class addShowSchedule(showProviderHome):
    template_name = "addShowSchedule.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404()

        providerObj = getProvider(request)
        mycourses = course.models.Course.objects.raw('SELECT * from course_course WHERE provider_id = ' + str(providerObj.id) + \
                                                     ' AND id NOT IN (SELECT parent_id from course_linkcourse)')

        courseDict = []
        for c in mycourses:
            courseDetails = course.algos.getCourseDetails(c.id, False)
            courseInfo = {}
            courseInfo['name'] = c.name
            courseInfo['details'] = courseDetails
            courseDict.append(courseInfo)

        kwargs['mycourses'] = courseDict
        return super().get(request, *args, **kwargs)