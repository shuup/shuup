# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import decimal
import pytest
from django.test import override_settings

from shuup.admin.modules.services.views import PaymentMethodEditView, ShippingMethodEditView
from shuup.core.models import (
    CountryLimitBehaviorComponent,
    FixedCostBehaviorComponent,
    GroupAvailabilityBehaviorComponent,
    OrderTotalLimitBehaviorComponent,
    PaymentMethod,
    ShippingMethod,
    StaffOnlyBehaviorComponent,
    WaivingCostBehaviorComponent,
    WeightLimitsBehaviorComponent,
)
from shuup.testing.factories import (
    get_default_customer_group,
    get_default_payment_method,
    get_default_shipping_method,
    get_default_shop,
)
from shuup.testing.utils import apply_request_middleware


def get_default_behavior_settings():
    return {
        FixedCostBehaviorComponent.__name__.lower(): {
            "description__en": "Fixed cost test",
            "price_value": 1,
            "id": "",
        },
        WaivingCostBehaviorComponent.__name__.lower(): {
            "description__en": "Waiving cost test",
            "price_value": 1,
            "waive_limit_value": 1,
            "id": "",
        },
        "weight_based_price_ranges": {
            "description__en": "Weight based pricing test",
            "price_value": 1,
            "min_value": 1,
            "max_value": 2,
            "id": "",
        },
        WeightLimitsBehaviorComponent.__name__.lower(): {
            "min_weight": 0,
            "max_weight": 1,
            "id": "",
        },
        GroupAvailabilityBehaviorComponent.__name__.lower(): {"groups": [get_default_customer_group().pk]},
        StaffOnlyBehaviorComponent.__name__.lower(): {},
        OrderTotalLimitBehaviorComponent.__name__.lower(): {"min_price_value": 0, "max_price_value": 21},
        CountryLimitBehaviorComponent.__name__.lower(): {
            "available_in_countries": [
                "FI",
            ]
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
    behavior_settings = get_default_behavior_settings()

    for component_name, component_dict in behavior_settings.items():
        data.update(
            {
                "%s-MAX_NUM_FORMS" % component_name: 20,
                "%s-MIN_NUM_FORMS" % component_name: 0,
                "%s-INITIAL_FORMS" % component_name: 0,
                "%s-TOTAL_FORMS" % component_name: 1,
            }
        )
        if delete:
            data["%s-0-DELETE" % component_name] = "on"
        for field, value in component_dict.items():
            data["%s-0-%s" % (component_name, field)] = value
    return data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view,model,get_object,service_provider_attr",
    [
        (PaymentMethodEditView, PaymentMethod, get_default_payment_method, "payment_processor"),
        (ShippingMethodEditView, ShippingMethod, get_default_shipping_method, "carrier"),
    ],
)
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

        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        view(request, pk=object.pk)
        components_after = object.behavior_components.count()
        assert components_after == len(get_default_behavior_settings())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view,model,get_object,service_provider_attr",
    [
        (PaymentMethodEditView, PaymentMethod, get_default_payment_method, "payment_processor"),
        (ShippingMethodEditView, ShippingMethod, get_default_shipping_method, "carrier"),
    ],
)
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

        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        response = view(request, pk=object.pk)
        if hasattr(response, "render"):
            response.render()
        components_after = object.behavior_components.count()
        assert not components_after

        assert not WaivingCostBehaviorComponent.objects.first()
