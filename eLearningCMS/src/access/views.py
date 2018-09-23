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

from datetime import timedelta
from datetime import datetime

from profiles.signals import sendMail
User = get_user_model()
datetimeFormat = '%d/%m/%Y %H:%M:%S'
# device types 
MOBILE = 'mobile'
PC = 'pc'
TABLET = 'tablet'
BOT = 'bot'

# Create your views here.

# encrypt
# input : plain text,key,IV
# return: encrypted text , key , IV
def encrypt(clear_text,key=None,iv=None):
    tag_string = clear_text
    cipher_aes = ''
    if key == None and iv == None:
        key = get_random_bytes(AES.block_size)
        cipher_aes = AES.new(key, AES.MODE_GCM)
        iv = cipher_aes.nonce
    else:
        cipher_aes = AES.new(key, AES.MODE_GCM,iv)
    cipher_text = base64.b64encode(cipher_aes.encrypt(tag_string.encode()))
    return cipher_text.decode(),key,iv

# decrypt function
# input : encryptedText , key , IV
# return: plainText
def decrypt (encryptText,key,iv):
    miss = len(str(encryptText)) % AES.block_size
    dec_secret = AES.new(key, AES.MODE_GCM, iv)
    raw_decrypted = dec_secret.decrypt(base64.b64decode(encryptText.encode()))
    plaintext = raw_decrypted.decode().rstrip("\0")
    return plaintext

# return cookie value as dictionary
def createNewCookieValue(userId,deviceInfo):
    cookieDic = {}
    cookieDic['user'] = userId
    cookieDic['time'] = datetime.now().strftime(datetimeFormat)
    cookieDic['device_type'] = deviceInfo['device_type']
    cookieDic['browser'] = deviceInfo['browser']
    return cookieDic

def sendNotificationEmail(email,deviceInfo):
    return
    emailSubj = 'New Device has been added'
    emailBody = """
    Dear Student,
    Login from your device  """+ deviceInfo['device_type'] + """ and browser """ + deviceInfo['browser'] + """ has been added.
    Kindly note that a student is allowed to access
    only 2 devices.
    Thanks
    GyaanHive Team
    """
    sendMail(email, emailSubj,emailBody)

def sendAuthenticationEmail(httpProtocol,deviceObj, deviceInfo, userObj):
    key = base64.b64decode(str.split(deviceObj.key, "::")[0])
    iv = base64.b64decode(str.split(deviceObj.key, "::")[1])
    data = createNewCookieValue(userObj.id,deviceInfo)
    text = json.dumps(data)
    ciphertext = encrypt(text,key,iv)
    deviceObj.authTime = calendar.timegm(time.gmtime())
    deviceObj.save()
    queryArg = {}
    queryArg['cipher'] = ciphertext
    link = '{}://{}/access/authorize/{}?{}'.format(httpProtocol,profiles.signals.getHost(), userObj.id,urllib.parse.urlencode(queryArg))
    body = 'Authorize your device using the link ' + link
    print (link)
    #sendMail(userObj.email, 'GyaanHive Authorize Device',body)

'''
def sendAuthenticationEmail(httpProtocol,deviceObj, deviceInfo, userObj):
    key = get_random_bytes(16)
    cipher_aes = AES.new(key, AES.MODE_GCM)
    # sending deviceInfo hash to reduce length of Authentication mail
    deviceInfoHash = hashlib.md5(deviceInfo.encode()).hexdigest()
    deviceDict = {}
    deviceDict['device'] = deviceInfoHash
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
'''    
def parse_user_agents(request):
    user_agent = get_user_agent(request)
    data = {}
    #data["os"] = user_agent.os.family
    #data["os_version"] = user_agent.os.version_string
    data["browser"] = user_agent.browser.family
    #data["browser_version"] = user_agent.browser.version_string
    device_type = ''
    if user_agent.is_mobile:
        device_type = MOBILE
    elif user_agent.is_pc:
        device_type=PC
    elif user_agent.is_tablet:
        device_type=TABLET
    elif user_agent.is_bot:
        device_type=BOT
    data["device_type"] = device_type
    #data["device_family"] = user_agent.device.family
    #data["device_brand"] = user_agent.device.brand
    #data["device_model"] = user_agent.device.model
    return data

def verifyCookie(value,userid,deviceInfo,deviceObj,cookieDbTime):
    key = base64.b64decode(str.split(deviceObj.key, "::")[0])
    iv = base64.b64decode(str.split(deviceObj.key, "::")[1])
    plaintext = decrypt(value,key,iv)
    cookieInfo = json.loads(plaintext)
    cookieTime = cookieInfo['time']
    cTime = datetime.strptime(cookieTime,datetimeFormat)
    isExpired = False
    dInfoFromCookie = cookieInfo['device_type'] + ';' + cookieInfo['browser']
    if cookieInfo['user'] == userid and cookieInfo['time'] == cookieDbTime and dInfoFromCookie == deviceInfo:
        # check if update needed
        eTime = (cTime + timedelta(days=settings.USER_AUTH_COOKIE_UPDATE_IN_DAYS))
        if eTime < datetime.now():
            isExpired = True
        return True,isExpired
    return False,False

class allowDevice(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, userid, deviceinfo, *args, **kwargs):
        devices = models.UserCookieInfo.objects.filter(user_id=userid)
        userObj = User.objects.filter(id=userid)[0]
        # check number of devices registered with this user
        deviceCount = len(devices)
        #device_data = mergeAndGetDeviceInfo(request,deviceinfo)
        myDeviceMap = {}
        # if no device registered, then register first device
        device_data = parse_user_agents(request)
        deviceDetected = device_data['device_type']+';'+device_data['browser']
        if deviceCount == 0:
            deviceObj = models.UserCookieInfo(user=userObj)
            cookieValue = createNewCookieValue(userid,device_data)
            ciphertext,key,iv = encrypt(json.dumps(cookieValue))
            deviceObj.key = base64.b64encode(key).decode() + "::" + base64.b64encode(iv).decode()
            deviceObj.device = deviceDetected
            deviceObj.cookieTime = cookieValue['time']
            deviceObj.save()
            resp = HttpResponse(True)
            resp.set_signed_cookie(settings.USER_AUTH_COOKIE, ciphertext,max_age=settings.USER_AUTH_COOKIE_AGE)
            sendNotificationEmail(userObj.email,device_data)
            return resp

        # In this case atleast one of the device is already registered
        # check cookie here
        deviceObj = devices[0]
        deviceList = str.split(deviceObj.device, "--")
        key = base64.b64decode(str.split(deviceObj.key, "::")[0])
        iv = base64.b64decode(str.split(deviceObj.key, "::")[1])
        cookieTimeList = str.split(deviceObj.cookieTime, "--")
        # Try to validate cookie with the incoming request
        i = 0
        while i < len(deviceList) :
            myDeviceMap[str.split(deviceList[i],';')[0]] = 1
            if deviceList[i] == deviceDetected:
                if settings.USER_AUTH_COOKIE in request.COOKIES.keys():
                    # cookie found, then validate
                    cookieValue = request.get_signed_cookie(settings.USER_AUTH_COOKIE)
                    isValid,isExpired = verifyCookie(cookieValue,userid,deviceDetected,deviceObj,cookieTimeList[i])
                    # check cookie validity and set new cookie if required here
                    resp = HttpResponse(isValid)
                    if isValid and isExpired:
                        # update cookie here
                        cookieValue = createNewCookieValue(userid,device_data)
                        cookieTimeList[i] = cookieValue['time']
                        ciphertext = encrypt(json.dumps(cookieValue),key,iv)
                        deviceObj.cookieTime = "--".join(cookieTimeList)
                        resp.set_signed_cookie(settings.USER_AUTH_COOKIE, ciphertext,max_age=settings.USER_AUTH_COOKIE_AGE)
                        deviceObj.save()
                    return resp
                elif deviceObj.miss <= settings.NUMBER_OF_COOKIE_MISS:
                    # user must have deleted his cookie, or 
                    # same device info found the shared login id
                    # create new cookie
                    deviceObj.miss = deviceObj.miss + 1
                    cookieValue = createNewCookieValue(userid,device_data)
                    cookieTimeList[i] = cookieValue['time']
                    ciphertext = encrypt(json.dumps(cookieValue),key,iv)
                    resp = HttpResponse(True)
                    deviceObj.cookieTime = "--".join(cookieTimeList)
                    resp.set_signed_cookie(settings.USER_AUTH_COOKIE, ciphertext,max_age=settings.USER_AUTH_COOKIE_AGE)
                    deviceObj.save()
                    sendNotificationEmail(userObj.email,device_data)
                    return resp
                else:
                    return HttpResponse(False)
            i = i+1

        # user has exceeded number of supported devices
        if len(deviceList) == settings.NUMBER_ALLOWED_DEVICES:
            return HttpResponse(False)
        
        # ensure only one browser per device support
        if device_data['device_type'] in myDeviceMap :
            try:
                sendAuthenticationEmail(request.scheme,deviceObj, device_data, userObj)
            except:
                return HttpResponse(False)
            deviceObj.miss = deviceObj.miss + 1
            deviceObj.save()
            return HttpResponse(False)
            

        # add new device
        cookieValue = createNewCookieValue(userid,device_data)
        deviceObj.device = deviceObj.device + '--' + deviceDetected
        deviceObj.cookieTime = deviceObj.cookieTime + '--' + cookieValue['time']
        ciphertext = encrypt(json.dumps(cookieValue),key,iv)
        resp = HttpResponse(True)
        resp.set_signed_cookie(settings.USER_AUTH_COOKIE, ciphertext,max_age=settings.USER_AUTH_COOKIE_AGE)
        deviceObj.save()
        sendNotificationEmail(userObj.email,device_data)
        return resp
'''        
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
'''
class authorizeDevice(LoginRequiredMixin, generic.TemplateView):
    template_name = 'authorize.html'
    http_method_names = ['get']

    def get(self, request, userid, *args, **kwargs):
        # check logged in user is same as the one giving the authorize url
        if userid != request.user.id:
            raise Http404()

        deviceObj = models.UserCookieInfo.objects.filter(user_id=userid)[0]

        device_data = parse_user_agents(request)
        deviceDetected = device_data['device_type']+';'+device_data['browser']

        # check if the link is accessed within 5 minutes of its generation
        if int(deviceObj.authTime) < int(calendar.timegm(time.gmtime())) - 300:
            raise Http404()
        devicecipher = (request.GET['cipher'])

        key = base64.b64decode(str.split(deviceObj.key, "::")[0])
        iv = base64.b64decode(str.split(deviceObj.key, "::")[1])
        plaintext = decrypt(devicecipher,key,iv)
        deviceInfo = json.loads(plaintext.decode())

        # check details are same as in the auth mail
        if deviceInfo['user'] != userid or deviceInfo['device_type'] != device_data['device_type'] or deviceInfo['browser'] != device_data['browser']:
            raise Http404()
        
        # update device here 
        # remove old info for this device and update new one
        cookieValue = createNewCookieValue(userid,device_data)     
        deviceList = str.split(deviceObj.device, "--")
        cookieTimeList = str.split(deviceObj.cookieTime, "--")

        i = 0
        while i < len(deviceList):
            if str.split(deviceList[i],';')[0] == str.split(deviceDetected,';')[0] :
                deviceList[i] = deviceDetected
                cookieTimeList[i] = cookieValue['time']
                deviceObj.cookieTime = "--".join(cookieTimeList)
                deviceObj.device = "--".join(deviceList)
                break
            i=i+1    

        ciphertext = encrypt(json.dumps(cookieValue),key,iv)
        deviceObj.save()
        kwargs["device_type"] = device_data['device_type']
        kwargs["browser"] = device_data['browser']
        resp = super().get(request, userid, *args, **kwargs)
        resp.set_signed_cookie(settings.USER_AUTH_COOKIE, ciphertext,max_age=settings.USER_AUTH_COOKIE_AGE)
        sendNotificationEmail(userObj.email,device_data)
        return resp

class challengeAccept(generic.TemplateView):
    http_method_names = ['get']

    def get(self, request, challengeBytes, deviceinfo, *args, **kwargs):
        devices = models.UserDevice.objects.filter(challenge=challengeBytes)
        if len(devices) == 0:
            return HttpResponse(False)
        
        device_data = mergeAndGetDeviceInfo(request,deviceinfo)
        
        deviceObj = devices[0]
        d1 = json.loads(deviceObj.candidate)['device']
        d2 = data2_md5 = hashlib.md5(device_data.encode()).hexdigest()
        #if not same(json.loads(deviceObj.candidate)['device'], device_data):
        #    return HttpResponse(False)
        if d1 != d2:
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

