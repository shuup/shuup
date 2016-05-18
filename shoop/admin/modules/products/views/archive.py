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

from shoop.core.models import Product


class ProductArchiveView(DetailView):
    model = Product
    context_object_name = "product"

    def get(self, request, *args, **kwargs):
        product = self.get_object()
        product.archive(user=request.user)
        messages.success(request, _(u"%s has been archived.") % product)
        return HttpResponseRedirect(reverse("shoop_admin:product.list"))
