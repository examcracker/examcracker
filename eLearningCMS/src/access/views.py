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
#import pdb

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
    dec_secret = AES.new(key, AES.MODE_GCM, iv)
    encodeText = encryptText.encode()
    b64decode = base64.b64decode(encodeText)
    raw_decrypted = dec_secret.decrypt(b64decode)
    #plaintext = raw_decrypted.decode().rstrip("\0")
    plaintext = raw_decrypted.decode()
    return plaintext

# takes json data as input
def getHash(data):
    data_md5 = hashlib.md5(data.encode()).hexdigest()
    return data_md5

# convert python dictionary to json string
def getDictToJson(data):
    jsondata = json.dumps(data,sort_keys=True)
    return jsondata

# return cookie value as dictionary
def createNewCookieValue(userId,deviceInfo):
    cookieDic = {}
    cookieDic['user'] = userId
    cookieDic['time'] = datetime.now().strftime(datetimeFormat)
    cookieDic['device_type'] = deviceInfo['device_type']
    cookieDic['browser'] = deviceInfo['browser']
    return cookieDic

def sendNotificationEmail(email,deviceInfo):
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
    authData = {}
    authData['user'] = deviceObj.user_id
    authData['device_type'] = deviceInfo['device_type']
    authData['browser'] = deviceInfo['browser']
    jsontext = getDictToJson(authData)
    ciphertext = getHash(jsontext)
    deviceObj.authTime = calendar.timegm(time.gmtime())
    deviceObj.save()
    queryArg = {}
    queryArg['cipher'] = ciphertext
    link = '{}://{}/access/authorize/{}?{}'.format(httpProtocol,profiles.signals.getHost(), userObj.id,urllib.parse.urlencode(queryArg))
    body = 'Authorize your device using the link ' + link
    #print (link)
    sendMail(userObj.email, 'GyaanHive Authorize Device',body)

  
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

def verifyCookie(value,userid,deviceInfo,deviceObj,cookieDbTime,dbHash):
    # create data from received request
    cookieDic = {}
    cookieDic['user'] = userid
    cookieDic['time'] = cookieDbTime
    cookieDic['device_type'] = deviceInfo['device_type']
    cookieDic['browser'] = deviceInfo['browser']
    jsontext = getDictToJson(cookieDic)
    # hash from user request
    hashjsontext = getHash(jsontext)

    # hash stored in db
    dbHash = dbHash
    cTime = datetime.strptime(cookieDbTime,datetimeFormat)
    isExpired = False
    #dInfoFromCookie = cookieInfo['device_type'] + ';' + cookieInfo['browser']
    if dbHash == value and value == hashjsontext:
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
            ciphertext = getHash(getDictToJson(cookieValue))
            deviceObj.key = ciphertext
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
        keyList = str.split(deviceObj.key, "--")
        cookieTimeList = str.split(deviceObj.cookieTime, "--")
        # Try to validate cookie with the incoming request
        i = 0
        while i < len(deviceList) :
            myDeviceMap[str.split(deviceList[i],';')[0]] = 1
            if deviceList[i] == deviceDetected:
                if settings.USER_AUTH_COOKIE in request.COOKIES.keys():
                    # cookie found, then validate
                    cookieValue = request.get_signed_cookie(settings.USER_AUTH_COOKIE)
                    isValid,isExpired = verifyCookie(cookieValue,userid,device_data,deviceObj,cookieTimeList[i],keyList[i])
                    # check cookie validity and set new cookie if required here
                    resp = HttpResponse(isValid)
                    if isValid and isExpired:
                        # update cookie here
                        cookieValue = createNewCookieValue(userid,device_data)
                        ciphertext = getHash(getDictToJson(cookieValue))
                        cookieTimeList[i] = cookieValue['time']                      
                        keyList[i] = ciphertext
                        deviceObj.cookieTime = "--".join(cookieTimeList)
                        deviceObj.key = "--".join(keyList)
                        resp.set_signed_cookie(settings.USER_AUTH_COOKIE, ciphertext,max_age=settings.USER_AUTH_COOKIE_AGE)
                        deviceObj.save()
                    return resp
                elif deviceObj.miss <= settings.NUMBER_OF_COOKIE_MISS:
                    # user must have deleted his cookie, or 
                    # same device info found the shared login id
                    # create new cookie
                    resp = HttpResponse(True)
                    deviceObj.miss = deviceObj.miss + 1
                    cookieValue = createNewCookieValue(userid,device_data)
                    ciphertext = getHash(getDictToJson(cookieValue))
                    cookieTimeList[i] = cookieValue['time']                      
                    keyList[i] = ciphertext
                    deviceObj.cookieTime = "--".join(cookieTimeList)
                    deviceObj.key = "--".join(keyList)
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
        ciphertext = getHash(getDictToJson(cookieValue))
        deviceObj.key = deviceObj.key + '--' + ciphertext
        resp = HttpResponse(True)
        resp.set_signed_cookie(settings.USER_AUTH_COOKIE, ciphertext,max_age=settings.USER_AUTH_COOKIE_AGE)
        deviceObj.save()
        sendNotificationEmail(userObj.email,device_data)
        return resp

class authorizeDevice(LoginRequiredMixin, generic.TemplateView):
    template_name = 'authorize.html'
    http_method_names = ['get']

    def get(self, request, userid, *args, **kwargs):
        # check logged in user is same as the one giving the authorize url
        if userid != request.user.id:
            raise Http404()

        deviceObj = models.UserCookieInfo.objects.filter(user_id=userid)[0]
        # check if the link is accessed within 5 minutes of its generation
        if (deviceObj.authTime == 0) or int(deviceObj.authTime) < int(calendar.timegm(time.gmtime())) - 300:
            # Auth link expired/Invalid
            raise Http404()
        
        deviceInfo = parse_user_agents(request)
        deviceDetected = deviceInfo['device_type']+';'+deviceInfo['browser']        
        # auth data from verification link
        devicecipher = (request.GET['cipher'])

        # lets construct auth data from request
        authData = {}
        authData['user'] = userid
        authData['device_type'] = deviceInfo['device_type']
        authData['browser'] = deviceInfo['browser']
        jsontext = getDictToJson(authData)
        hashtext = getHash(jsontext)
        #verify auth data
        if hashtext != devicecipher:
            raise Http404()

        # update device here 
        # remove old info for this device and update new one
        cookieValue = createNewCookieValue(userid,deviceInfo)
        ciphertext = getHash(getDictToJson(cookieValue))
        deviceList = str.split(deviceObj.device, "--")
        cookieTimeList = str.split(deviceObj.cookieTime, "--")
        keyList = str.split(deviceObj.key, "--")
        deviceObj.authTime = 0
        i = 0
        while i < len(deviceList):
            if str.split(deviceList[i],';')[0] == str.split(deviceDetected,';')[0] :
                deviceList[i] = deviceDetected
                keyList[i] = ciphertext
                cookieTimeList[i] = cookieValue['time']
                deviceObj.cookieTime = "--".join(cookieTimeList)
                deviceObj.device = "--".join(deviceList)
                deviceObj.key = "--".join(keyList)
                deviceObj.save()
                break
            i=i+1

        kwargs["device_type"] = deviceInfo['device_type']
        kwargs["browser"] = deviceInfo['browser']
        resp = super().get(request, userid, *args, **kwargs)
        resp.set_signed_cookie(settings.USER_AUTH_COOKIE, ciphertext,max_age=settings.USER_AUTH_COOKIE_AGE)
        userObj = User.objects.filter(id=userid)[0]
        sendNotificationEmail(userObj.email,deviceInfo)
        return resp
