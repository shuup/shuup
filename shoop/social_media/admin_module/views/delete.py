# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import DetailView

from shoop.admin.utils.urls import get_model_url
from shoop.social_media.models import SocialMediaLink


class SocialMediaLinkDeleteView(DetailView):
    model = SocialMediaLink
    context_object_name = "social_media_link"

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(get_model_url(self.get_object()))

    def post(self, request, *args, **kwargs):
        social_media_link = self.get_object()
        url = social_media_link.url
        social_media_link.delete()
        messages.success(request, _(u"%s has been deleted.") % url)
        return HttpResponseRedirect(reverse("shoop_admin:social_media_link.list"))
