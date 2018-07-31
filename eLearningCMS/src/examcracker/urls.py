from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.conf.urls import url
import profiles.urls
import accounts.urls
import provider.urls
import student.urls
import course.urls
import access.urls
import notification.urls
from . import views

# Personalized admin site settings like title and header
admin.site.site_title = 'ExamCracker Site Admin'
admin.site.site_header = 'ExamCracker Administration'

urlpatterns = [
    url(r'^paypal/', include('paypal.standard.ipn.urls')),
    url(r'^payment/', include('payments.urls')),
    path('', views.HomePage.as_view(), name='home'),
    path('about/', views.AboutPage.as_view(), name='about'),
    path('users/', include(profiles.urls)),
    path('admin/', admin.site.urls),
    path('contact/', views.ContactPage.as_view(), name='contact'),
    path('pricing/', views.PricingPage.as_view(), name='pricing'),
    path('blog/', views.BlogPage.as_view(), name='blog'),
    path('courses/', views.CoursesPage.as_view(), name='courses'),
    path('provider/',include(provider.urls)),
    path('student/',include(student.urls)),
    path('access/',include(access.urls)),
    path('notification/', include(notification.urls)),
    path('course/',include(course.urls)),
    path('home/', views.HomePage.as_view(), name='home'),
    path('searchResults/', views.SearchResultsPage.as_view(), name='searchResults'),
    path('', include(accounts.urls)),
]

# User-uploaded files like profile pics need to be served in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Include django debug toolbar if DEBUG is on
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
