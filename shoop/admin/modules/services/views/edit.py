# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.db.transaction import atomic

from shoop.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shoop.admin.modules.services.base_form_part import (
    PaymentMethodBaseFormPart, ShippingMethodBaseFormPart
)
from shoop.admin.modules.services.behavior_form_part import \
    BehaviorComponentFormPart
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.apps.provides import get_provide_objects
from shoop.core.models import PaymentMethod, ShippingMethod


class ServiceEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = None
    template_name = "shoop/admin/services/edit.jinja"
    context_object_name = "shipping_method"
    base_form_part_classes = []  # Override in subclass
    provide_key = "service_behavior_component_form"

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)

    def get_form_parts(self, object):
        form_parts = super(ServiceEditView, self).get_form_parts(object)
        if not object.pk:
            return form_parts
        for form in get_provide_objects(self.provide_key):
            form_parts.append(self._get_behavior_form_part(form, object))
        return form_parts

    def _get_behavior_form_part(self, form, object):
        return BehaviorComponentFormPart(self.request, form, form._meta.model.__name__.lower(), object)


class ShippingMethodEditView(ServiceEditView):
    model = ShippingMethod
    base_form_part_classes = [ShippingMethodBaseFormPart]


class PaymentMethodEditView(ServiceEditView):
    model = PaymentMethod
    base_form_part_classes = [PaymentMethodBaseFormPart]
