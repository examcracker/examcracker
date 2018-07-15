from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from paypal.standard.forms import PayPalPaymentsForm
from django.views.decorators.csrf import csrf_exempt
from django.http import QueryDict
from django.http import Http404
import urllib
from . import models
import course
import student
import profiles

def getStudent(request):
    return student.models.Student.objects.filter(user_id=request.user.id)[0]

@csrf_exempt
def payment_done(request):
    studentObj = getStudent(request)
    cartObjs = models.Cart.objects.filter(student_id=studentObj.id).filter(checkout=True)

    for obj in cartObjs:
        enrolledCourseObj = course.models.EnrolledCourse()
        enrolledCourseObj.student = studentObj
        enrolledCourseObj.course = course.models.Course.objects.filter(id=obj.course_id)[0]
        enrolledCourseObj.save()
        obj.delete()

    return render(request, 'payment/done.html')

@csrf_exempt
def payment_canceled(request):
    studentObj = getStudent(request)
    cartObjs = models.Cart.objects.filter(student_id=studentObj.id).filter(checkout=True)

    for obj in cartObjs:
        obj.checkout = False;
        obj.save()

    return render(request, 'payment/canceled.html')

def payment_process(request):
    studentObj = getStudent(request)
    host = request.get_host()
    courses = urllib.parse.unquote(request.GET['id'])
    courselist = str.split(courses, " ")

    totalCost = 0
    courseList = []

    for c in courselist:
        try:
            c = int(c)
        except:
            continue
        courseObj = course.models.Course.objects.filter(id=c)[0]
        courseList.append(courseObj)
        totalCost = totalCost + courseObj.cost

        cartObj = models.Cart.objects.filter(student_id=studentObj.id).filter(course_id=courseObj.id)

    paypal_dict = {
        'business': settings.PAYPAL_RECEIVER_EMAIL ,
        'amount': totalCost,
        'item_name': "Courses Enrolled",
        'invoice': "Invoice for " + str(request.user.name),
        'currency_code': 'USD',
        'notify_url': 'http://{}{}'.format(host, reverse('paypal-ipn')),
        'return_url': 'http://{}{}'.format(host, reverse('payments:done')),
        'cancel_return': 'http://{}{}'.format(host, reverse('payments:canceled')),
    }

    form = PayPalPaymentsForm(initial=paypal_dict)
    return render(request, 'payment/process.html', {'form': form, 'courses': courseList})

class Cart(LoginRequiredMixin, generic.TemplateView):
    template_name = 'my_cart.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        if request.user.is_staff:
            raise Http404()
        studentObj = student.models.Student.objects.filter(user_id=request.user.id)[0]
        courses = course.models.Course.objects.raw('SELECT * from course_course WHERE id IN (SELECT course_id from payments_cart WHERE student_id = ' + str(studentObj.id) + ')')
        kwargs["courses"] = courses
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.user.is_staff:
            raise Http404()
        studentObj = getStudent(request)
        selectedCourses = request.POST.getlist('courses[]')
        if len(selectedCourses) == 0:
            return redirect("payments:my_cart")

        if "delete" in request.POST:
            for course in selectedCourses:
                cartObj = models.Cart.objects.filter(student_id=studentObj.id).filter(course_id=course)[0]
                cartObj.delete()
            return redirect("payments:my_cart")
        else:
            coursesStr = ''
            for course in selectedCourses:
                cartObj = models.Cart.objects.filter(student_id=studentObj.id).filter(course_id=course)[0]
                cartObj.checkout = True
                cartObj.save()
                coursesStr = coursesStr + " " + course

            query_dictionary = QueryDict('', mutable=True)
            query_dictionary.update({'id': coursesStr})
            url = '{base_url}?{querystring}'.format(base_url=reverse("payments:process"),
                                                querystring=query_dictionary.urlencode())
            return redirect(url)
