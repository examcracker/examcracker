from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import generic
from django.http import HttpResponse
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from django.conf import settings
import base64
import json
import calendar
import time
import profiles
from . import models

User = get_user_model()

# Create your views here.

def same(d1, d2):
    o1 = json.loads(d1)
    o2 = json.loads(d2)
    c1 = str.split(o1['loc'], ",")
    c2 = str.split(o2['loc'], ",")
    if o1['browser'] == o2['browser'] and o1['os'] == o2['os'] and int(float(c1[0])) == int(float(c2[0])) and int(float(c1[1])) == int(float(c2[1])):
        return False
    return False

def sendAuthenticationEmail(deviceObj, deviceInfo, userObj):
    key = get_random_bytes(16)
    cipher_aes = AES.new(key, AES.MODE_GCM)

    deviceDict = {}
    deviceDict['device'] = deviceInfo
    deviceDict['user'] = userObj.id
    text = json.dumps(deviceDict)
    ciphertext = cipher_aes.encrypt(text.encode())

    deviceObj.key = base64.b64encode(key).decode() + "::" + base64.b64encode(cipher_aes.nonce).decode()
    deviceObj.time = calendar.timegm(time.gmtime())
    deviceObj.save()

    link = 'http://{}/{}/authorize/{}'.format(profiles.signals.getHost(), userObj.id, base64.b64encode(ciphertext).decode())
    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_HOST_USER
    msg['To'] = 'kghoshnitk@gmail.com' #userObj.email
    msg['Subject'] = 'GyaanHive Authorize Device'
    body = 'Authorize your device using the link ' + link
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.sendmail(settings.EMAIL_HOST_USER, 'kghoshnitk@gmail.com', msg.as_string())
    
    
class allowDevice(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, userid, deviceinfo, *args, **kwargs):
        devices = models.UserDevice.objects.filter(user_id=userid)
        if len(devices) == 0:
            userObj = User.objects.filter(id=userid)[0]
            deviceObj = models.UserDevice(user=userObj)
            deviceObj.device = deviceinfo
            deviceObj.save()
            return HttpResponse(True)

        deviceObj = devices[0]
        deviceList = str.split(deviceObj.device, "--")

        for device in deviceList:
            if same(device, deviceinfo) == True:
                return HttpResponse(True)

        userObj = User.objects.filter(id=userid)[0]
        if len(deviceList) < 3:
            deviceObj.device = deviceObj.device + "--" + deviceinfo
            deviceObj.save()
            return HttpResponse(True)

        # send authentication email
        sendAuthenticationEmail(deviceObj, deviceinfo, userObj)
        return HttpResponse(False)

        
