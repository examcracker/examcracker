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
from course.views import getCartCourses,fillCartCourses
from student.views import getStudent
import re
# Try kghoshnitk@gmail.com and sane password
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
        obj.checkout = False
        obj.save()

    return render(request, 'payment/canceled.html')

class payment_process(LoginRequiredMixin,generic.TemplateView):
    template_name = 'payment/process.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        studentObj = getStudent(request)
        host = request.get_host()
        totalCost,allCourses = getCartCourses(request)
        kwargs["tcost"] = totalCost
        kwargs["cartCourses"] = allCourses
        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL ,
            'amount': totalCost,
            'item_name': "Courses Enrolled",
            'invoice': "Invoice for " + str(request.user.name),
            'currency_code': 'USD',
            'notify_url': '{}://{}{}'.format(request.scheme,host, reverse('paypal-ipn')),
            'return_url': '{}://{}{}'.format(request.scheme,host, reverse('payments:done')),
            'cancel_return': '{}://{}{}'.format(request.scheme,host, reverse('payments:canceled')),
            }

        form = PayPalPaymentsForm(initial=paypal_dict)
        kwargs["form"] = form
        return super().get(request, *args, **kwargs)

class Cart(LoginRequiredMixin, fillCartCourses):
    template_name = 'my_cart.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        if request.user.is_staff:
            raise Http404()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.user.is_staff:
            raise Http404()
        studentObj = getStudent(request)
        cartObjs = models.Cart.objects.filter(student_id=studentObj.id)
        coursesStr = ''
        for cartObj in cartObjs:
            cartObj.checkout = True
            cartObj.save()
            #coursesStr = coursesStr + " " + str(cartObj.course_id)
        #query_dictionary = QueryDict('', mutable=True)
        #query_dictionary.update({'id': coursesStr})
        #url = '{base_url}?{querystring}'.format(base_url=reverse("payments:process"),
        #                                        querystring=query_dictionary.urlencode())
        url = "payments:process"
        return redirect(url)

def get_referer_view(request, default=None):
    # if the user typed the url directly in the browser's address bar
    referer = request.META.get('HTTP_REFERER')
    if not referer:
        return default
    # remove the protocol and split the url at the slashes
    httpProtocol = request.scheme
    referer = re.sub('^'+httpProtocol+'?:\/\/', '', referer).split('/')
    # add the slash at the relative path's view and finished
    referer = u'/' + u'/'.join(referer[1:])
    return referer

def add_to_cart(studentObj,courseId):
    courseObj = course.models.Course.objects.filter(id=courseId)[0]
    cartCourseObj = models.Cart.objects.filter(course_id=courseId,student_id=studentObj)
    if not cartCourseObj.exists()  :
        cart = models.Cart()
        cart.student = studentObj
        cart.course = courseObj
        cart.save()

class addToCart(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, id, *args, **kwargs):
        refered_url =  get_referer_view(request)
        if refered_url is None:
            return redirect("home")
        courseid = id
        studentObj = getStudent(request)
        if studentObj:
            add_to_cart(studentObj,courseid)
        # check the source from where add to cart is called
        if 'course' in refered_url and  'coursePage' in refered_url:
            url = "course:coursePage"
            return redirect(url,courseid)
        url = "home"
        return redirect(url)

def delete_from_cart(studentObj,courseId):
    cartCourseObj = models.Cart.objects.filter(student_id=studentObj)
    cartCnt = len(cartCourseObj)
    cartCourseObj = cartCourseObj.filter(course_id=courseId)
    if  cartCourseObj.exists():
        cartCourseObj.delete()
        cartCnt = cartCnt-1
    return cartCnt

class deleteFromCart(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, id, *args, **kwargs):
        refered_url =  get_referer_view(request)
        if refered_url is None:
            return redirect("home")
        courseid = id
        studentObj = getStudent(request)
        cartCnt = -1
        if studentObj:
            cartCnt = delete_from_cart(studentObj,courseid)
        # check the source from where delete from cart is called
        if 'course' in refered_url and  'coursePage' in refered_url:
            url = "course:coursePage"
            return redirect(url,courseid)
        elif 'payment' in refered_url and cartCnt > 0:
            if 'cart' in refered_url:
                url = "payments:my_cart"
            elif 'process' in refered_url:
                url = "payments:process"
        else:
            url = "home" 
        return redirect(url)
