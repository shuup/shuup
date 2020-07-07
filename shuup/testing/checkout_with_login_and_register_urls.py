# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

from shuup.front.views.checkout import CheckoutViewWithLoginAndRegister

if django.VERSION < (2, 0):
    urlpatterns = [
        url(r'^checkout/$', CheckoutViewWithLoginAndRegister.as_view(), name='checkout'),
        url(r'^checkout/(?P<phase>.+)/$', CheckoutViewWithLoginAndRegister.as_view(), name='checkout'),
        url(r'^admin/', include(admin.site.urls)),
        url(r'^sa/', include('shuup.admin.urls', namespace="shuup_admin", app_name="shuup_admin")),
        url(r'^', include('shuup.front.urls', namespace="shuup", app_name="shuup")),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    from django.urls import path
    urlpatterns = [
        url(r'^checkout/$', CheckoutViewWithLoginAndRegister.as_view(), name='checkout'),
        url(r'^checkout/(?P<phase>.+)/$', CheckoutViewWithLoginAndRegister.as_view(), name='checkout'),
        path('admin/', admin.site.urls),
        url(r'^sa/', include('shuup.admin.urls', namespace="shuup_admin")),
        url(r'^', include('shuup.front.urls', namespace="shuup")),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
