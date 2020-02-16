# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import DetailView

from shuup.admin.utils.urls import get_model_url
from shuup.front.apps.carousel.models import Carousel


class CarouselDeleteView(DetailView):
    model = Carousel
    context_object_name = "carousel"

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(get_model_url(self.get_object()))

    def post(self, request, *args, **kwargs):
        carousel = self.get_object()
        name = carousel.name
        carousel.delete()
        messages.success(request, _(u"%s has been deleted.") % name)
        return HttpResponseRedirect(reverse("shuup_admin:carousel.list"))
