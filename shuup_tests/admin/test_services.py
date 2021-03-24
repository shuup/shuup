# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django import forms
from django.conf import settings
from django.db.models import ProtectedError
from django.test import override_settings
from django.utils.encoding import force_text

from shuup.admin.modules.services.base_form_part import ServiceBaseFormPart
from shuup.admin.modules.services.forms import PaymentMethodForm, ShippingMethodForm
from shuup.admin.modules.services.views import PaymentMethodEditView, ShippingMethodEditView
from shuup.admin.utils.urls import get_model_url
from shuup.apps.provides import override_provides
from shuup.core.models import Label, PaymentMethod, ShippingMethod
from shuup.testing.factories import (
    create_empty_order,
    get_custom_carrier,
    get_custom_payment_processor,
    get_default_payment_method,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_default_tax_class,
)
from shuup.testing.utils import apply_request_middleware

DEFAULT_BEHAVIOR_FORMS = [
    "shuup.admin.modules.services.forms.FixedCostBehaviorComponentForm",
    "shuup.admin.modules.services.forms.WaivingCostBehaviorComponentForm",
    "shuup.admin.modules.services.forms.WeightLimitsBehaviorComponentForm",
]

DEFAULT_BEHAVIOR_FORM_PARTS = ["shuup.admin.modules.services.weight_based_pricing.WeightBasedPricingFormPart"]


def get_form_parts(request, view, object):
    with override_provides("service_behavior_component_form", DEFAULT_BEHAVIOR_FORMS):
        with override_provides("service_behavior_component_form_part", DEFAULT_BEHAVIOR_FORM_PARTS):
            initialized_view = view(request=request, kwargs={"pk": object.pk})
            return initialized_view.get_form_parts(object)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view,get_object",
    [(PaymentMethodEditView, get_default_payment_method), (ShippingMethodEditView, get_default_shipping_method)],
)
def test_services_edit_view_formsets(rf, admin_user, view, get_object):
    get_default_shop()
    object = get_object()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    form_parts = get_form_parts(request, view, object)
    # form parts should include forms, form parts and plus one for the base form
    assert len(form_parts) == (len(DEFAULT_BEHAVIOR_FORMS) + len(DEFAULT_BEHAVIOR_FORM_PARTS) + 1)


@pytest.mark.django_db
@pytest.mark.parametrize("view", [PaymentMethodEditView, ShippingMethodEditView])
def test_services_edit_view_formsets_in_new_mode(rf, admin_user, view):
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    form_parts = get_form_parts(request, view, view.model())
    assert len(form_parts) == 1
    assert issubclass(form_parts[0].__class__, ServiceBaseFormPart)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "form_class,get_object,service_provider_attr",
    [
        (PaymentMethodForm, get_default_payment_method, "payment_processor"),
        (ShippingMethodForm, get_default_shipping_method, "carrier"),
    ],
)
def test_choice_identifier_in_method_form(rf, admin_user, form_class, get_object, service_provider_attr):
    object = get_object()
    assert object.pk

    service_provider = getattr(object, service_provider_attr)
    request = apply_request_middleware(rf.get("/"), user=admin_user)

    form = form_class(instance=object, languages=settings.LANGUAGES, request=request)
    assert "choice_identifier" in form.fields
    assert len(form.fields["choice_identifier"].choices) == len(service_provider.get_service_choices())
    assert form.fields["choice_identifier"].widget.__class__ == forms.Select

    assert getattr(object, service_provider_attr)
    setattr(object, service_provider_attr, None)

    # No service provider so no choice_identifier-field
    form = form_class(instance=object, languages=settings.LANGUAGES, request=request)
    assert "choice_identifier" in form.fields
    assert len(form.fields["choice_identifier"].choices) == 0  # Choices for default provider


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view,model,service_provider_attr,get_provider",
    [
        (PaymentMethodEditView, PaymentMethod, "payment_processor", get_custom_payment_processor),
        (ShippingMethodEditView, ShippingMethod, "carrier", get_custom_carrier),
    ],
)
def test_method_creation(rf, admin_user, view, model, service_provider_attr, get_provider):
    """
    To make things little bit more simple let's use only english as
    an language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        view = view.as_view()
        service_provider_field = "base-%s" % service_provider_attr
        data = {
            service_provider_field: get_provider().id,
            "base-choice_identifier": "manual",
            "base-name__en": "Custom method",
            "base-shop": get_default_shop().id,
            "base-tax_class": get_default_tax_class().id,
            "base-enabled": True,
        }
        # Default provider CustomCarrier/CustomPaymentProcessor should be set in form init
        methods_before = model.objects.count()
        url = "/?provider=%s" % get_provider().id
        request = apply_request_middleware(rf.post(url, data=data), user=admin_user)
        response = view(request, pk=None)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code in [200, 302]
        assert model.objects.count() == (methods_before + 1)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view,model,service_provider_attr,get_provider",
    [
        (PaymentMethodEditView, PaymentMethod, "payment_processor", get_custom_payment_processor),
        (ShippingMethodEditView, ShippingMethod, "carrier", get_custom_carrier),
    ],
)
def test_method_creation_with_labels(rf, admin_user, view, model, service_provider_attr, get_provider):
    """
    To make things little bit more simple let's use only english as
    an language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        for identifier, name in [("pickup", "Pickup"), ("delivery", "Delivery"), ("airmail", "Airmail")]:
            label = Label.objects.create(identifier=identifier, name=name)
            assert label.name == name
            assert "%s" % label == name

        view = view.as_view()
        service_provider_field = "base-%s" % service_provider_attr
        data = {
            service_provider_field: get_provider().id,
            "base-choice_identifier": "manual",
            "base-name__en": "Custom method",
            "base-shop": get_default_shop().id,
            "base-tax_class": get_default_tax_class().id,
            "base-enabled": True,
            "base-labels": Label.objects.values_list("pk", flat=True),
        }
        # Default provider CustomCarrier/CustomPaymentProcessor should be set in form init
        methods_before = model.objects.count()
        url = "/?provider=%s" % get_provider().id
        request = apply_request_middleware(rf.post(url, data=data), user=admin_user)
        response = view(request, pk=None)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code in [200, 302]
        assert model.objects.count() == (methods_before + 1)
        assert model.objects.last().labels.count() == Label.objects.count()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view,model,get_object,service_provider_attr",
    [
        (PaymentMethodEditView, PaymentMethod, get_default_payment_method, "payment_processor"),
        (ShippingMethodEditView, ShippingMethod, get_default_shipping_method, "carrier"),
    ],
)
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
            "base-choice_identifier": "manual",
        }
        methods_before = model.objects.count()
        # Behavior components is tested at shuup.tests.admin.test_service_behavior_components
        with override_provides("service_behavior_component_form", []):
            with override_provides("service_behavior_component_form_part", []):
                request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
                response = view(request, pk=object.pk)
                if hasattr(response, "render"):
                    response.render()
                assert response.status_code in [200, 302]

        assert model.objects.count() == methods_before
        assert model.objects.get(pk=object.pk).choice_identifier == "manual"


def check_for_delete(view, request, object):
    can_delete = object.can_delete()
    delete_url = get_model_url(object, "delete")
    response = view(request, pk=object.pk)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code in [200, 302]
    assert bool(delete_url in force_text(response.content)) == can_delete


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view_cls,get_method,method_attr",
    [
        (PaymentMethodEditView, get_default_payment_method, "payment_method"),
        (ShippingMethodEditView, get_default_shipping_method, "shipping_method"),
    ],
)
def test_delete_toolbar_button(rf, admin_user, view_cls, get_method, method_attr):
    method = get_method()
    assert method.can_delete()
    view = view_cls.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    check_for_delete(view, request, method)

    # Create order for method and test the can_delete and edit view
    order = create_empty_order()
    setattr(order, method_attr, method)
    order.save()
    assert not method.can_delete()
    check_for_delete(view, request, method)

    # Make sure that the actual delete is also blocked
    with pytest.raises(ProtectedError):
        method.delete()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view,model,service_provider_attr,get_provider",
    [
        (PaymentMethodEditView, PaymentMethod, "payment_processor", get_custom_payment_processor),
        (ShippingMethodEditView, ShippingMethod, "carrier", get_custom_carrier),
    ],
)
def test_method_creation_with_supplier(rf, admin_user, view, model, service_provider_attr, get_provider):
    provider = get_provider()
    supplier = get_default_supplier()

    # add supplier to the service provider
    provider.supplier = supplier
    provider.save()

    with override_settings(LANGUAGES=[("en", "en")]):
        view = view.as_view()
        service_provider_field = "base-%s" % service_provider_attr
        data = {
            service_provider_field: provider.id,
            "base-choice_identifier": "manual",
            "base-name__en": "Custom method",
            "base-shop": get_default_shop().id,
            "base-tax_class": get_default_tax_class().id,
            "base-enabled": True,
        }
        # Default provider CustomCarrier/CustomPaymentProcessor should be set in form init
        methods_before = model.objects.count()
        url = "/?provider=%s" % provider.id
        request = apply_request_middleware(rf.post(url, data=data), user=admin_user)
        response = view(request, pk=None)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code == 200
        # nothing created as the service provider has supplier and we don't have access to it
        assert model.objects.count() == methods_before
