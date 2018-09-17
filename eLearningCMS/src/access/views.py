from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.views import generic
from django.http import HttpResponse
from django.http import Http404
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.parse
import smtplib
from django.conf import settings
import base64
import json
import calendar
import time
import profiles
import notification
from . import models
from django_user_agents.utils import get_user_agent 
import hashlib

User = get_user_model()

# Create your views here.

def same(d1, d2):
    data1_md5 = hashlib.md5(d1.encode()).hexdigest()
    data2_md5 = hashlib.md5(d2.encode()).hexdigest()
    if data1_md5 == data2_md5:
        return True
    #o1 = json.loads(d1)
    #o2 = json.loads(d2)
    #c1 = str.split(o1['loc'], ",")
    #c2 = str.split(o2['loc'], ",")
    #if o1['browser'] == o2['browser'] and o1['os'] == o2['os'] and int(float(c1[0])) == int(float(c2[0])) and int(float(c1[1])) == int(float(c2[1])):
    '''
    if o1['browser'] == o2['browser'] and \
       o1['browser_version'] == o2['browser_version'] and \
       o1['os'] == o2['os'] and \
       o1['os_version'] == o2['os_version'] and \
       o1['device_type'] == o2['device_type'] and \
       o1['device_family'] == o2['device_family'] and \
       o1['device_brand'] == o2['device_brand'] and \
       o1['device_model'] == o2['device_model']:
        return True
    '''
    return False


def sendAuthenticationEmail(httpProtocol,deviceObj, deviceInfo, userObj):
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

    queryArg = {}
    queryArg['cipher'] = base64.b64encode(ciphertext).decode()

    link = '{}://{}/access/authorize/{}?{}'.format(httpProtocol,profiles.signals.getHost(), userObj.id, urllib.parse.urlencode(queryArg))
    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_HOST_USER
    msg['To'] = userObj.email
    msg['Subject'] = 'GyaanHive Authorize Device'
    body = 'Authorize your device using the link ' + link
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.sendmail(settings.EMAIL_HOST_USER, userObj.email, msg.as_string())
    
def parse_user_agents(request):
    user_agent = get_user_agent(request)
    data = {}
    data["os"] = user_agent.os.family
    data["os_version"] = user_agent.os.version_string
    data["browser"] = user_agent.browser.family
    data["browser_version"] = user_agent.browser.version_string
    device_type = ''
    if user_agent.is_mobile:
        device_type = 'mobile'
    elif user_agent.is_pc:
        device_type='pc'
    elif user_agent.is_tablet:
        device_type='tablet'
    elif user_agent.is_bot:
        device_type='bot'
    data["device_type"] = device_type
    data["device_family"] = user_agent.device.family
    data["device_brand"] = user_agent.device.brand
    data["device_model"] = user_agent.device.model
    #json_data = json.dumps(data)
    return data

def mergeAndGetDeviceInfo(request,deviceinfo):
    data1 = {}
    data1 = parse_user_agents(request)
    data2 = json.loads(deviceinfo)
    data1.update(data2)
    json_data = json.dumps(data1)
    return json_data

class allowDevice(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, userid, deviceinfo, *args, **kwargs):
        devices = models.UserDevice.objects.filter(user_id=userid)
        device_data = mergeAndGetDeviceInfo(request,deviceinfo)
        if len(devices) == 0:
            userObj = User.objects.filter(id=userid)[0]
            deviceObj = models.UserDevice(user=userObj)
            deviceObj.device = device_data
            deviceObj.save()
            return HttpResponse(True)
        deviceObj = devices[0]
        if deviceObj.device:
            deviceList = str.split(deviceObj.device, "--")
            for device in deviceList:
                if same(device, device_data) == True:
                    return HttpResponse(True)

        userObj = User.objects.filter(id=userid)[0]
        if not deviceObj.device or len(deviceList) < 3:
            if not deviceObj.device:
                deviceObj.device = device_data
            else:
                deviceObj.device = deviceObj.device + "--" + device_data
            deviceObj.save()
            return HttpResponse(True)

        sendAuthenticationEmail(request.scheme,deviceObj, device_data, userObj)
        return HttpResponse(False)

class authorizeDevice(LoginRequiredMixin, generic.TemplateView):
    template_name = 'authorize.html'
    http_method_names = ['get']

    def get(self, request, userid, *args, **kwargs):
        # check logged in user is same as the one giving the authorize url
        if userid != request.user.id:
            raise Http404()

        deviceObj = models.UserDevice.objects.filter(user_id=userid)[0]

        # check if the link is accessed within 5 minutes of its generation
        if int(deviceObj.time) < int(calendar.timegm(time.gmtime())) - 300:
            raise Http404()

        devicecipher = urllib.parse.unquote(request.GET['cipher'])

        key = base64.b64decode(str.split(deviceObj.key, "::")[0])
        nonce = base64.b64decode(str.split(deviceObj.key, "::")[1])
        ciphertext = base64.b64decode(devicecipher)

        plain_aes = AES.new(key, AES.MODE_GCM, nonce)
        plaintext = plain_aes.decrypt(ciphertext)

        deviceInfo = json.loads(plaintext.decode())

        # check if user id is same as the one in encrypted message
        if deviceInfo['user'] != userid:
            raise Http404()

        challengeBytes = base64.b64encode(get_random_bytes(16)).decode()
        deviceObj.challenge = challengeBytes
        deviceObj.candidate = plaintext.decode()
        deviceObj.save()

        kwargs["challenge"] = challengeBytes
        return super().get(request, userid, *args, **kwargs)

class challengeAccept(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, challengeBytes, deviceinfo, *args, **kwargs):
        devices = models.UserDevice.objects.filter(challenge=challengeBytes)
        if len(devices) == 0:
            return HttpResponse(False)
        
        device_data = mergeAndGetDeviceInfo(request,deviceinfo)
        
        deviceObj = devices[0]

        if not same(json.loads(deviceObj.candidate)['device'], device_data):
            return HttpResponse(False)

        registered = str.split(deviceObj.device, "--")

        registered[0] = registered[1]
        registered[1] = registered[2]
        registered[2] = device_data

        deviceStr = registered[0] + "--" + registered[1] + "--" + registered[2]
        deviceObj.device = deviceStr
        deviceObj.save()

        notification.models.notify(deviceObj.user_id, notification.models.DEVICE_ADDED, notification.models.INFO)
        return HttpResponse(True)

