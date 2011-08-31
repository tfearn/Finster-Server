from django.conf.urls.defaults import *
from web.api import checkin, getcheckins, getuser, loginwithfb, follow, unfollow, getuserfollowers, getuserfollowing, isfollowinguser, gettrending, finduser, getfriends, getleaderboard, getuserlastcheckins

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^finster/', include('finster.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    (r'^api/checkin$', checkin),
    (r'^api/getcheckins$', getcheckins),
    (r'^api/getuser$', getuser),
    (r'^api/loginUsingFacebook$', loginwithfb),
    (r'^api/followuser$', follow),
    (r'^api/unfollowuser$', unfollow),
    (r'^api/getuserfollowers$', getuserfollowers),
    (r'^api/getuserfollowing$', getuserfollowing),
    (r'^api/isfollowinguser$', isfollowinguser),
    (r'^api/gettrending$', gettrending),
    (r'^api/finduser$', finduser),
    (r'^api/getfriends$', getfriends),
    (r'^api/getleaderboard$', getleaderboard),
    (r'^api/getuserlastcheckins$', getuserlastcheckins),
)
