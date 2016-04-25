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
from shoop.admin.toolbar import get_default_edit_toolbar
from shoop.admin.utils.urls import get_model_url
from shoop.admin.utils.views import CreateOrUpdateView
from shoop.apps.provides import get_provide_objects
from shoop.core.models import PaymentMethod, ShippingMethod


class ServiceEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = None  # Override in subclass
    template_name = "shoop/admin/services/edit.jinja"
    context_object_name = "service"
    base_form_part_classes = []  # Override in subclass
    form_provide_key = "service_behavior_component_form"
    form_part_provide_key = "service_behavior_component_form_part"

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)

    def get_form_parts(self, object):
        form_parts = super(ServiceEditView, self).get_form_parts(object)
        if not object.pk:
            return form_parts
        for form in get_provide_objects(self.form_provide_key):
            form_parts.append(self._get_behavior_form_part(form, object))
        for form_class in get_provide_objects(self.form_part_provide_key):
            form_parts.append(form_class(self.request, object))
        return form_parts

    def _get_behavior_form_part(self, form, object):
        return BehaviorComponentFormPart(self.request, form, form._meta.model.__name__.lower(), object)

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        object = self.get_object()
        delete_url = get_model_url(object, "delete") if object.pk else None
        return get_default_edit_toolbar(self, save_form_id, delete_url=(delete_url if object.can_delete() else None))


class ShippingMethodEditView(ServiceEditView):
    model = ShippingMethod
    base_form_part_classes = [ShippingMethodBaseFormPart]


class PaymentMethodEditView(ServiceEditView):
    model = PaymentMethod
    base_form_part_classes = [PaymentMethodBaseFormPart]
