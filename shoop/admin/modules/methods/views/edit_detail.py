# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView

from shoop.core.models import PaymentMethod, ShippingMethod
from shoop.utils.excs import Problem
from shoop.utils.importing import load


class _BaseMethodDetailView(DetailView):
    model = None  # Overridden below
    title = _(u"Edit Details")

    def dispatch(self, request, *args, **kwargs):
        # This view only dispatches further to the method module's own detail view class
        object = self.get_object()
        module = object.module
        if not module.admin_detail_view_class:
            raise Problem("Module %s has no admin detail view" % module.name)
        if isinstance(module.admin_detail_view_class, six.text_type):
            view_class = load(module.admin_detail_view_class)
        else:
            view_class = module.admin_detail_view_class
        kwargs["object"] = object
        return view_class(model=self.model).dispatch(request, *args, **kwargs)


class ShippingMethodEditDetailView(_BaseMethodDetailView):
    model = ShippingMethod


class PaymentMethodEditDetailView(_BaseMethodDetailView):
    model = PaymentMethod
