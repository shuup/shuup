# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.test import override_settings

from shoop.admin.modules.services.views import (
    PaymentMethodEditView, ShippingMethodEditView
)
from shoop.core.models import (
    FixedCostBehaviorComponent, PaymentMethod, ShippingMethod,
    WaivingCostBehaviorComponent, WeightLimitsBehaviorComponent
)
from shoop.testing.factories import (
    get_default_payment_method, get_default_shipping_method, get_default_shop
)
from shoop.testing.utils import apply_request_middleware


DEFAULT_BEHAVIOR_SETTINGS = {
    FixedCostBehaviorComponent: {
        "description__en": "Fixed cost test",
        "price_value": 1,
        "id": "",
    },
    WaivingCostBehaviorComponent: {
        "description__en": "Waiving cost test",
        "price_value": 1,
        "waive_limit_value": 1,
        "id": "",
    },
    WeightLimitsBehaviorComponent: {
        "min_weight": 0,
        "max_weight": 1,
        "id": "",
    },
}


def get_default_data(object, service_provider_attr, service_provider_attr_field, delete=False):
    data = {
        "base-name__en": object.name,
        "base-shop": object.shop.id,
        "base-tax_class": object.tax_class.id,
        "base-enabled": True,
        service_provider_attr_field: getattr(object, service_provider_attr).pk,
        "base-choice_identifier": "manual",
    }

    data.update(get_default_component_form_data(delete=delete))
    return data


def get_default_component_form_data(delete=False):
    data = {}
    behavior_settings = DEFAULT_BEHAVIOR_SETTINGS

    for component, component_dict in behavior_settings.items():
        component_name = component.__name__.lower()
        data.update({
            "%s-MAX_NUM_FORMS" % component_name: 20,
            "%s-MIN_NUM_FORMS" % component_name: 0,
            "%s-INITIAL_FORMS" % component_name: 0,
            "%s-TOTAL_FORMS" % component_name: 1,
        })
        if delete:
            data["%s-0-DELETE" % component_name] = "on"
        for field, value in component_dict.items():
            data["%s-0-%s" % (component_name, field)] = value
    return data


@pytest.mark.django_db
@pytest.mark.parametrize("view,model,get_object,service_provider_attr", [
    (PaymentMethodEditView, PaymentMethod, get_default_payment_method, "payment_processor"),
    (ShippingMethodEditView, ShippingMethod, get_default_shipping_method, "carrier")
])
def test_behavior_add_save(rf, admin_user, view, model, get_object, service_provider_attr):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    get_default_shop()
    with override_settings(LANGUAGES=[("en", "en")]):
        object = get_object()
        view = view.as_view()
        service_provider_attr_field = "base-%s" % service_provider_attr

        data = get_default_data(object, service_provider_attr, service_provider_attr_field)
        components_before = object.behavior_components.count()
        assert not components_before

        request = apply_request_middleware(rf.post("/", data=data, user=admin_user))
        view(request, pk=object.pk)
        components_after = object.behavior_components.count()
        assert components_after == len(DEFAULT_BEHAVIOR_SETTINGS)


@pytest.mark.django_db
@pytest.mark.parametrize("view,model,get_object,service_provider_attr", [
    (PaymentMethodEditView, PaymentMethod, get_default_payment_method, "payment_processor"),
    (ShippingMethodEditView, ShippingMethod, get_default_shipping_method, "carrier")
])
def test_behavior_delete_save(rf, admin_user, view, model, get_object, service_provider_attr):
    """
    Only testing one initial behavior component
    """
    get_default_shop()
    with override_settings(LANGUAGES=[("en", "en")]):
        object = get_object()
        view = view.as_view()
        service_provider_attr_field = "base-%s" % service_provider_attr

        component = WeightLimitsBehaviorComponent.objects.create(min_weight=0, max_weight=1)
        object.behavior_components.add(component)
        components_before = object.behavior_components.count()
        assert components_before == 1

        data = get_default_data(object, service_provider_attr, service_provider_attr_field, delete=True)
        data["weightlimitsbehaviorcomponent-0-id"] = component.id
        data["weightlimitsbehaviorcomponent-INITIAL_FORMS"] = 1
        data["weightlimitsbehaviorcomponent-TOTAL_FORMS"] = 2

        request = apply_request_middleware(rf.post("/", data=data, user=admin_user))
        response = view(request, pk=object.pk)
        if hasattr(response, "render"):
            response.render()
        components_after = object.behavior_components.count()
        assert not components_after

        assert not WaivingCostBehaviorComponent.objects.first()
