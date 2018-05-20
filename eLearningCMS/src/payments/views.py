from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from paypal.standard.forms import PayPalPaymentsForm
from django.views.decorators.csrf import csrf_exempt
import course

@csrf_exempt
def payment_done(request):
    return render(request, 'payment/done.html')

@csrf_exempt
def payment_canceled(request):
    return render(request, 'payment/canceled.html')

def payment_process(request):
    host = request.get_host()
    courseid = request.GET['id']
    courseObj = course.models.Course.objects.filter(id=courseid)[0]

    paypal_dict = {
        'business': settings.PAYPAL_RECEIVER_EMAIL ,
        'amount': courseObj.cost,
        'item_name': courseObj.name,
        'invoice': courseObj.name,
        'currency_code': 'INR',
        'notify_url': 'http://{}{}'.format(host, reverse('paypal-ipn')),
        'return_url': 'http://{}{}'.format(host, reverse('payments:done')),
        'cancel_return': 'http://{}{}'.format(host, reverse('payments:canceled')),
    }
    form = PayPalPaymentsForm(initial=paypal_dict)
    return render(request, 'payment/process.html', {'form': form })
