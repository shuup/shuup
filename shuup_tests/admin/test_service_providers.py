# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from django.db.models.deletion import ProtectedError
from django.test import override_settings

from shuup.admin.modules.service_providers.views import ServiceProviderEditView
from shuup.apps.provides import override_provides
from shuup.core.models import CustomCarrier, CustomPaymentProcessor
from shuup.testing.factories import get_default_payment_method, get_default_shipping_method, get_default_shop
from shuup.testing.models import PseudoPaymentProcessor
from shuup.testing.utils import apply_all_middleware


def get_bs_object_for_view(request, view, user, object=None):
    """
    Help function to get BeautifulSoup object from the html rendered
    by the edit view.

    Also override ``service_provider_admin_form`` here to enable
    ``PseudoPaymentProcessor``
    """
    with override_provides(
        "service_provider_admin_form",
        [
            "shuup.testing.service_forms.PseudoPaymentProcessorForm",
            "shuup.admin.modules.service_providers.forms:CustomCarrierForm",
            "shuup.admin.modules.service_providers.forms:CustomPaymentProcessorForm",
        ],
    ):
        request = apply_all_middleware(request, user=user)
        response = view(request, pk=object.pk if object else None)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code in [200, 302]
        return BeautifulSoup(response.content)


@pytest.mark.parametrize(
    "sp_model,type_param",
    [(None, None), (CustomCarrier, "shuup.customcarrier"), (CustomPaymentProcessor, "shuup.custompaymentprocessor")],
)
def test_new_service_providers_type_select(rf, admin_user, sp_model, type_param):
    """
    Test `ServiceProvideEditView`` with different types of
    ``ServiceProvider`` subclasses. Make sure that view is rendered
    and creating new object works.

    To make things little bit more simple let's use only english as
    an language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        get_default_shop()
        view = ServiceProviderEditView.as_view()
        url = "/"
        if type_param:
            url += "?type=%s" % type_param
        soup = get_bs_object_for_view(rf.get(url), view, admin_user)
        selected_type = soup.find("select", attrs={"id": "id_type"}).find("option", selected=True)["value"]
        if type_param:
            assert type_param == selected_type
        else:
            assert selected_type in [
                "shuup.customcarrier",
                "shuup.custompaymentprocessor",
                "shuup_testing.pseudopaymentprocessor",
            ]

        if sp_model:
            name = "Some provider"
            data = {"type": type_param, "name__en": name, "enabled": True}
            if selected_type == "shuup.custompaymentprocessor":
                data["rounding_quantize"] = "0.05"
                data["rounding_mode"] = "ROUND_HALF_UP"
            provider_count = sp_model.objects.count()
            get_bs_object_for_view(rf.post(url, data=data), view, admin_user)
            assert sp_model.objects.count() == provider_count + 1


def test_invalid_service_provider_type(rf, admin_user):
    """
    Test ServiceProvideEditView with invalid type parameter.

    Pre 1.11 Django should have the first one selected and
    post 1.11 Django there shouldn't be nothing selected.
    This seems to come directly through Django so we are
    fine with this behavior change.
    """
    get_default_shop()
    view = ServiceProviderEditView.as_view()
    url = "/?type=SomethingThatIsNotProvided"

    soup = get_bs_object_for_view(rf.get(url), view, admin_user)
    provider_form = soup.find("form", attrs={"id": "service_provider_form"})
    type_select = provider_form.find("select", attrs={"id": "id_type"})
    options = []
    for option in type_select.findAll("option"):
        options.append(
            {
                "selected": bool(option.get("selected")),
                "value": option["value"],
            }
        )

    assert [x["selected"] for x in options] == [False, False, False]


@pytest.mark.parametrize(
    "type,extra_inputs",
    [
        ("shuup.custompaymentprocessor", ["rounding_quantize"]),
        ("shuup_testing.pseudopaymentprocessor", ["bg_color", "fg_color"]),
    ],
)
def test_new_service_provider_form_fields(rf, admin_user, type, extra_inputs):
    """
    Test `ServiceProvideEditView`` fields in new mode. Based on type
    different input-fields should be visible.

    To make things little bit more simple let's use only english as
    an language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        base_inputs = ["csrfmiddlewaretoken", "name__en", "enabled", "logo"]
        get_default_shop()
        view = ServiceProviderEditView.as_view()
        soup = get_bs_object_for_view(rf.get("?type=%s" % type), view, admin_user)
        provider_form = soup.find("form", attrs={"id": "service_provider_form"})
        rendered_fields = []
        for input_field in provider_form.findAll("input"):
            rendered_fields.append(input_field["name"])

        assert rendered_fields == (base_inputs + extra_inputs)


@pytest.mark.parametrize(
    "sp_model,extra_inputs",
    [
        (CustomCarrier, []),
        (CustomPaymentProcessor, ["rounding_quantize"]),
        (PseudoPaymentProcessor, ["bg_color", "fg_color"]),
    ],
)
def test_service_provide_edit_view(rf, admin_user, sp_model, extra_inputs):
    """
    Test that ``ServiceProvideEditView`` works with existing
    ``ServiceProvider`` subclasses

    To make things little bit more simple let's use only english as
    an language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        base_inputs = ["csrfmiddlewaretoken", "name__en", "enabled", "logo"]
        get_default_shop()
        view = ServiceProviderEditView.as_view()
        provider_name = "some name"
        service_provider = sp_model.objects.create(name=provider_name)
        soup = get_bs_object_for_view(rf.get("/"), view, admin_user, object=service_provider)
        provider_form = soup.find("form", attrs={"id": "service_provider_form"})
        rendered_fields = []
        for input_field in provider_form.findAll("input"):
            rendered_fields.append(input_field["name"])

        assert rendered_fields == (base_inputs + extra_inputs)
        assert provider_form.find("input", attrs={"name": "name__en"})["value"] == provider_name


@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_object,service_provider_attr",
    [(get_default_shipping_method, "carrier"), (get_default_payment_method, "payment_processor")],
)
def test_delete(get_object, service_provider_attr):
    method = get_object()
    assert method.enabled
    service_provider = getattr(method, service_provider_attr)
    assert service_provider

    with pytest.raises(ProtectedError):
        service_provider.delete()
