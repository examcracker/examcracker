from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
import profiles.urls
import accounts.urls
import provider.urls
import student.urls
from . import views

# Personalized admin site settings like title and header
admin.site.site_title = 'ExamCracker Site Admin'
admin.site.site_header = 'ExamCracker Administration'

urlpatterns = [
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
    path('home/', views.HomePage.as_view(), name='home'),
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
