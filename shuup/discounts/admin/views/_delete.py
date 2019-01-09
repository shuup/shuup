# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import DetailView

from shuup.admin.shop_provider import get_shop
from shuup.discounts.models import Discount


class DiscountDeleteView(DetailView):
    model = Discount

    def get_queryset(self):
        return Discount.objects.filter(shops=get_shop(self.request))

    def post(self, request, *args, **kwargs):
        discount = self.get_object()
        discount.delete()
        messages.success(request, _("%s has been deleted.") % discount)
        return HttpResponseRedirect(reverse("shuup_admin:discounts.list"))
