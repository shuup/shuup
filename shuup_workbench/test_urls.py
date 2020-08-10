# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

"""
Modify these only for Shuup tests. For testing modify urls.py instead.
"""
urlpatterns = [
    path(r'^admin/', admin.site.urls),
    url(r'^sa/', include('shuup.admin.urls', namespace="shuup_admin")),
    url(r'^', include('shuup.front.urls', namespace="shuup")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
