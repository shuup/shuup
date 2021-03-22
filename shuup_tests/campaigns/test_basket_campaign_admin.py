# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
# test that admin actually saves catalog
import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from shuup.apps.provides import override_provides
from shuup.campaigns.admin_module.form_parts import BasketBaseFormPart
from shuup.campaigns.admin_module.forms import FreeProductLineForm
from shuup.campaigns.admin_module.views import BasketCampaignEditView
from shuup.campaigns.models.basket_conditions import BasketTotalProductAmountCondition
from shuup.campaigns.models.basket_effects import BasketDiscountAmount
from shuup.campaigns.models.campaigns import BasketCampaign
from shuup.testing.factories import get_default_product, get_default_shop
from shuup.testing.utils import apply_request_middleware

DEFAULT_CONDITION_FORMS = [
    "shuup.campaigns.admin_module.forms:BasketTotalProductAmountConditionForm",
    "shuup.campaigns.admin_module.forms:BasketTotalAmountConditionForm",
    "shuup.campaigns.admin_module.forms:ProductsInBasketConditionForm",
    "shuup.campaigns.admin_module.forms:ContactGroupBasketConditionForm",
    "shuup.campaigns.admin_module.forms:ContactBasketConditionForm",
]

DEFAULT_DISCOUNT_EFFECT_FORMS = [
    "shuup.campaigns.admin_module.forms:BasketDiscountAmountForm",
    "shuup.campaigns.admin_module.forms:BasketDiscountPercentageForm",
]

DEFAULT_LINE_EFFECT_FORMS = [
    "shuup.campaigns.admin_module.forms:FreeProductLineForm",
]


def get_form_parts(request, view, object):
    with override_provides("campaign_basket_condition", DEFAULT_CONDITION_FORMS):
        with override_provides("campaign_basket_discount_effect_form", DEFAULT_DISCOUNT_EFFECT_FORMS):
            with override_provides("campaign_basket_line_effect_form", DEFAULT_LINE_EFFECT_FORMS):
                initialized_view = view(request=request, kwargs={"pk": object.pk})
                return initialized_view.get_form_parts(object)


@pytest.mark.django_db
def test_admin_campaign_edit_view_works(rf, admin_user):
    shop = get_default_shop()
    view_func = BasketCampaignEditView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    campaign = BasketCampaign.objects.create(name="test campaign", active=True, shop=shop)
    response = view_func(request, pk=campaign.pk)
    assert campaign.name in response.rendered_content

    response = view_func(request, pk=None)
    assert response.rendered_content


@pytest.mark.django_db
def test_campaign_new_mode_view_formsets(rf, admin_user):
    view = BasketCampaignEditView
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    form_parts = get_form_parts(request, view, view.model())
    assert len(form_parts) == 1
    assert issubclass(form_parts[0].__class__, BasketBaseFormPart)


@pytest.mark.django_db
def test_campaign_edit_view_formsets(rf, admin_user):
    view = BasketCampaignEditView
    shop = get_default_shop()
    object = BasketCampaign.objects.create(name="test campaign", active=True, shop=shop)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    form_parts = get_form_parts(request, view, object)
    # form parts should include forms plus one for the base form
    assert len(form_parts) == (8 + 1)


@pytest.mark.django_db
def test_campaign_creation(rf, admin_user):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        view = BasketCampaignEditView.as_view()
        data = {
            "base-name": "Test Campaign",
            "base-public_name__en": "Test Campaign",
            "base-shop": get_default_shop().id,
            "base-active": True,
            "base-basket_line_text": "Test campaign activated!",
        }
        campaigns_before = BasketCampaign.objects.count()
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        response = view(request, pk=None)
        assert response.status_code in [200, 302]
        assert BasketCampaign.objects.count() == (campaigns_before + 1)


@pytest.mark.django_db
def test_campaign_edit_save(rf, admin_user):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    with override_settings(LANGUAGES=[("en", "en")]):
        shop = get_default_shop()
        object = BasketCampaign.objects.create(name="test campaign", active=True, shop=shop)
        object.save()
        view = BasketCampaignEditView.as_view()
        new_name = "Test Campaign"
        assert object.name != new_name
        data = {
            "base-name": new_name,
            "base-public_name__en": "Test Campaign",
            "base-shop": get_default_shop().id,
            "base-active": True,
            "base-basket_line_text": "Test campaign activated!",
        }
        methods_before = BasketCampaign.objects.count()
        # Conditions and effects is tested separately
        with override_provides("campaign_basket_condition", []):
            with override_provides("campaign_basket_discount_effect_form", []):
                with override_provides("campaign_basket_line_effect_form", []):
                    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
                    response = view(request, pk=object.pk)
                    assert response.status_code in [200, 302]

        assert BasketCampaign.objects.count() == methods_before
        assert BasketCampaign.objects.get(pk=object.pk).name == new_name


@pytest.mark.django_db
def test_rules_and_effects(rf, admin_user):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    get_default_shop()
    with override_settings(LANGUAGES=[("en", "en")]):
        shop = get_default_shop()
        object = BasketCampaign.objects.create(name="test campaign", active=True, shop=shop)
        assert object.conditions.count() == 0
        assert object.discount_effects.count() == 0
        view = BasketCampaignEditView.as_view()
        data = {
            "base-name": "test campaign",
            "base-public_name__en": "Test Campaign",
            "base-shop": get_default_shop().id,
            "base-active": True,
            "base-basket_line_text": "Test campaign activated!",
        }
        with override_provides(
            "campaign_basket_condition", ["shuup.campaigns.admin_module.forms:BasketTotalProductAmountConditionForm"]
        ):
            with override_provides(
                "campaign_basket_discount_effect_form", ["shuup.campaigns.admin_module.forms:BasketDiscountAmountForm"]
            ):
                with override_provides("campaign_basket_line_effect_form", []):
                    data.update(get_products_in_basket_data())
                    data.update(get_free_product_data(object))
                    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
                    view(request, pk=object.pk)

        object.refresh_from_db()
        assert object.conditions.count() == 1
        assert object.discount_effects.count() == 1


def get_products_in_basket_data():
    rule_name = BasketTotalProductAmountCondition.__name__.lower()
    data = {
        "conditions_%s-MAX_NUM_FORMS" % rule_name: 2,
        "conditions_%s-MIN_NUM_FORMS" % rule_name: 0,
        "conditions_%s-INITIAL_FORMS" % rule_name: 0,
        "conditions_%s-TOTAL_FORMS" % rule_name: 1,
    }
    data["conditions_%s-0-%s" % (rule_name, "product_count")] = 20
    return data


def get_free_product_data(object):
    effect_name = BasketDiscountAmount.__name__.lower()
    data = {
        "effects_%s-MAX_NUM_FORMS" % effect_name: 2,
        "effects_%s-MIN_NUM_FORMS" % effect_name: 0,
        "effects_%s-INITIAL_FORMS" % effect_name: 0,
        "effects_%s-TOTAL_FORMS" % effect_name: 1,
    }
    data["effects_%s-0-%s" % (effect_name, "campaign")] = object.pk
    data["effects_%s-0-%s" % (effect_name, "discount_amount")] = 20
    return data


@pytest.mark.django_db
def test_free_product_line_form(rf, admin_user):
    with override_settings(LANGUAGES=[("en", "en")]):
        shop = get_default_shop()
        prod = get_default_product()
        object = BasketCampaign.objects.create(name="test campaign", active=True, shop=shop)
        object.save()
        data = {"campaign": object, "quantity": 0, "products": [prod.pk]}
        form = FreeProductLineForm()
        form.cleaned_data = data
        with pytest.raises(ValidationError):
            form.clean()
        data["quantity"] = 1
        form.cleaned_data = data
        form.clean()
