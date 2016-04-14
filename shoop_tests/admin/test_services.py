# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from django import forms
from django.conf import settings
from django.test import override_settings

from shoop.admin.modules.services.base_form_part import ServiceBaseFormPart
from shoop.admin.modules.services.forms import PaymentMethodForm, ShippingMethodForm
from shoop.admin.modules.services.views import (
    PaymentMethodEditView, ShippingMethodEditView
)
from shoop.apps.provides import override_provides
from shoop.core.models import PaymentMethod, ShippingMethod
from shoop.testing.factories import (
    get_default_payment_method, get_default_shipping_method, get_default_shop,
    get_default_tax_class
)
from shoop.testing.utils import apply_request_middleware


DEFAULT_BEHAVIOR_FORMS = [
    "shoop.admin.modules.services.forms.FixedCostBehaviorComponentForm",
    "shoop.admin.modules.services.forms.WaivingCostBehaviorComponentForm",
    "shoop.admin.modules.services.forms.WeightLimitsBehaviorComponentForm"
]


def get_form_parts(request, view, object):
    with override_provides("service_behavior_component_form", DEFAULT_BEHAVIOR_FORMS):
        initialized_view = view(request=request, kwargs={"pk": object.pk})
        return initialized_view.get_form_parts(object)


@pytest.mark.django_db
@pytest.mark.parametrize("view,get_object", [
    (PaymentMethodEditView, get_default_payment_method),
    (ShippingMethodEditView, get_default_shipping_method)
])
def test_services_edit_view_formsets(rf, admin_user, view, get_object):
    get_default_shop()
    object = get_object()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    form_parts = get_form_parts(request, view, object)
    assert len(form_parts) == (len(DEFAULT_BEHAVIOR_FORMS) + 1)  # plus one since the base form


@pytest.mark.django_db
@pytest.mark.parametrize("view", [PaymentMethodEditView, ShippingMethodEditView])
def test_services_edit_view_formsets_in_new_mode(rf, admin_user, view):
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    form_parts = get_form_parts(request, view, view.model())
    assert len(form_parts) == 1
    assert issubclass(form_parts[0].__class__, ServiceBaseFormPart)


@pytest.mark.django_db
@pytest.mark.parametrize("form_class,get_object,service_provider_attr", [
    (PaymentMethodForm, get_default_payment_method, "payment_processor"),
    (ShippingMethodForm, get_default_shipping_method, "carrier")
])
def test_choice_identifier_in_method_form(rf, admin_user, form_class, get_object, service_provider_attr):
    object = get_object()
    assert object.pk


    service_provider = getattr(object, service_provider_attr)
    form = form_class(instance=object, languages=settings.LANGUAGES)
    assert "choice_identifier" in form.fields
    assert len(form.fields["choice_identifier"].choices) == (len(service_provider.get_service_choices()) + 1)
    assert form.fields["choice_identifier"].widget.__class__ == forms.Select

    assert getattr(object, service_provider_attr)
    setattr(object, service_provider_attr, None)

    # No service provider so no choice_identifier-field
    form = form_class(instance=object, languages=settings.LANGUAGES)
    assert "choice_identifier" in form.fields
    assert len(form.fields["choice_identifier"].choices) == 0

    # Let's check cases when the object is not yet saved
    form = form_class(instance=object._meta.model(), languages=settings.LANGUAGES)
    assert "choice_identifier" in form.fields
    assert len(form.fields["choice_identifier"].choices) == 0


@pytest.mark.django_db
@pytest.mark.parametrize("view,model", [
    (PaymentMethodEditView, PaymentMethod),
    (ShippingMethodEditView, ShippingMethod)
])
def test_method_creation(rf, admin_user, view, model):
    """
    To make things little bit more simple let's use only english as
    an language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        view = view.as_view()
        data = {
            "base-name__en": "Custom method",
            "base-shop": get_default_shop().id,
            "base-tax_class": get_default_tax_class().id,
            "base-enabled": True,
        }
        methods_before = model.objects.count()
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        response = view(request, pk=None)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code in [200, 302]
        assert model.objects.count() == (methods_before + 1)


@pytest.mark.django_db
@pytest.mark.parametrize("view,model,get_object,service_provider_attr", [
    (PaymentMethodEditView, PaymentMethod, get_default_payment_method, "payment_processor"),
    (ShippingMethodEditView, ShippingMethod, get_default_shipping_method, "carrier")
])
def test_method_edit_save(rf, admin_user, view, model, get_object, service_provider_attr):
    """
    To make things little bit more simple let's use only english as
    an language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        object = get_object()
        object.choice_identifier = ""
        object.save()
        assert object.choice_identifier == ""
        view = view.as_view()
        service_provider_attr_field = "base-%s" % service_provider_attr
        data = {
            "base-name__en": object.name,
            "base-shop": object.shop.id,
            "base-tax_class": object.tax_class.id,
            "base-enabled": True,
            service_provider_attr_field: getattr(object, service_provider_attr).pk,
            "base-choice_identifier": "manual"
        }
        methods_before = model.objects.count()
        # Behavior components is tested at shoop.tests.admin.test_service_behavior_components
        with override_provides("service_behavior_component_form", []):
            request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
            response = view(request, pk=object.pk)
            if hasattr(response, "render"):
                response.render()
            assert response.status_code in [200, 302]
        assert model.objects.count() == methods_before
        assert model.objects.get(pk=object.pk).choice_identifier == "manual"
