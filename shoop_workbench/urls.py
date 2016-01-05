# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.conf.urls import include, patterns, url
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^sa/', include('shoop.admin.urls', namespace="shoop_admin", app_name="shoop_admin")),
    url(r'^api/', include('shoop.api.urls')),
    url(r'^', include('shoop.front.urls', namespace="shoop", app_name="shoop")),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
