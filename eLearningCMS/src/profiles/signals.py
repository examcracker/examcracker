from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import notification
from . import models

logger = logging.getLogger("project")

def getHost():
    if len(settings.ALLOWED_HOSTS) == 0:
        return 'localhost:8000'
    return settings.ALLOWED_HOSTS[0]

def sendMail(toEmail, emailSubj,emailBody):
    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_HOST_USER
    msg['To'] = toEmail
    msg['Subject'] = emailSubj
    body = emailBody
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.sendmail(settings.EMAIL_HOST_USER, toEmail, msg.as_string())

def sendVerificationMail(email, typeofuser, code):
    link = 'http://{}/{}/verifyEmail/{}'.format(getHost(), typeofuser, code)
    body = 'Verify your email using the link ' + link
    sendMail(email,'Welcome to GyaanHive',body)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_handler(sender, instance, created, **kwargs):
    if not created:
        return
    # Create the profile object, only if it is newly created
    profile = models.Profile(user=instance)
    profile.save()

    typeofuser = 'student'
    if instance.is_staff:
        typeofuser = 'provider'

    try:
        sendVerificationMail(instance.email, typeofuser, profile.slug)
    except:
        logger.error('Verification email could not be sent to {}.'.format(instance.email))
    notification.models.notify(instance.id, notification.models.EMAIL_NOT_VERIFIED, notification.models.WARNING, instance.email)
    logger.info('New user profile for {} created'.format(instance))
