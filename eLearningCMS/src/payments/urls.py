from django.urls import path
from django.conf.urls import url
from . import views

app_name = 'payments'

urlpatterns = [
    url(r'^process/$', views.payment_process, name='process'),
    url(r'^done/$', views.payment_done, name='done'),
    url(r'^canceled/$', views.payment_canceled, name='canceled'),
    path('cart', views.Cart.as_view(), name='my_cart')
]
