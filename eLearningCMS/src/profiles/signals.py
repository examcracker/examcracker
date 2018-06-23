from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from . import models

logger = logging.getLogger("project")

def sendVerificationMail(email, code):
    link = 'http://{}{}'.format('localhost:8000', code)

    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_ADMIN_ID
    msg['To'] = settings.SMTP_ADMIN_PASSWORD
    msg['Subject'] = 'Welcome to GyaanHive'
    body = 'Verify your email using the link ' + link
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(settings.SMTP_ADMIN_ID, settings.SMTP_ADMIN_PASSWORD)
    server.sendmail(settings.SMTP_ADMIN_ID, email, msg.as_string())


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_handler(sender, instance, created, **kwargs):
    if not created:
        return
    # Create the profile object, only if it is newly created
    profile = models.Profile(user=instance)
    profile.save()
    sendVerificationMail(instance.email, profile.slug)
    logger.info('New user profile for {} created'.format(instance))
