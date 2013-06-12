from django.conf.urls.defaults import *
from ocpuser.views import *
import django.contrib.auth

# Uncomment the next two lines to enable the admin:                        
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('ocpuser.views',
                       url(r'^profile/$', 'profile'),
                       url(r'^createproject/$', 'createproject'),
                       url(r'^updateproject/$', 'updateproject'),
                       url(r'^restore/$', 'restore'),
   
)
