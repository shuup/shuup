# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
# test that admin actually saves catalog
import pytest
from bs4 import BeautifulSoup
from django.http.response import Http404
from django.test import override_settings

from shuup.admin.supplier_provider import get_supplier
from shuup.apps.provides import override_provides
from shuup.campaigns.admin_module.views import BasketCampaignEditView, BasketCampaignListView
from shuup.campaigns.models.campaigns import BasketCampaign
from shuup.core.models import Supplier
from shuup.testing.factories import create_random_user, get_default_shop
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
def test_admin_campaign_edit_view_works_with_supplier(rf, admin_user):
    shop = get_default_shop()
    supplier = Supplier.objects.create(identifier=admin_user.username)
    view_func = BasketCampaignEditView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    campaign = BasketCampaign.objects.create(name="test campaign", active=True, shop=shop)
    response = view_func(request, pk=campaign.pk)
    assert campaign.name in response.rendered_content

    response = view_func(request, pk=None)
    assert response.rendered_content
    soup = BeautifulSoup(response.rendered_content)
    assert soup.find("select", {"id": "id_base-supplier"})

    supplier_provider = "shuup.testing.supplier_provider.UsernameSupplierProvider"
    with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC=supplier_provider):
        assert get_supplier(request) == supplier
        response = view_func(request, pk=None)
        assert response.rendered_content
        soup = BeautifulSoup(response.rendered_content)
        assert not soup.find("select", {"id": "id_base-supplier"})


@pytest.mark.django_db
def test_campaign_creation_for_supplier(rf, admin_user):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    shop = get_default_shop()
    supplier = Supplier.objects.create(identifier=admin_user.username)

    another_superuser = create_random_user(is_superuser=True, is_staff=True)
    supplier2 = Supplier.objects.create(identifier=another_superuser.username)

    supplier_provider = "shuup.testing.supplier_provider.UsernameSupplierProvider"
    with override_settings(LANGUAGES=[("en", "en")]):
        with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC=supplier_provider):
            view = BasketCampaignEditView.as_view()
            data = {
                "base-name": "Test Campaign",
                "base-public_name__en": "Test Campaign",
                "base-shop": shop.id,
                "base-active": True,
                "base-basket_line_text": "Test campaign activated!",
            }
            campaigns_before = BasketCampaign.objects.count()
            request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
            assert get_supplier(request) == supplier
            response = view(request, pk=None)
            assert response.status_code in [200, 302]
            assert BasketCampaign.objects.count() == (campaigns_before + 1)

            new_campaign = BasketCampaign.objects.filter(supplier=supplier).first()
            assert new_campaign

            # Another superuser shouldn't see this campaign
            request = apply_request_middleware(rf.post("/", data=data), user=another_superuser)
            assert get_supplier(request) == supplier2
            with pytest.raises(Http404):
                response = view(request, pk=new_campaign.pk)


def test_campaign_list_for_suppliers(rf, admin_user):
    """
    To make things little bit more simple let's use only english as
    a language.
    """
    shop = get_default_shop()

    superuser1 = create_random_user(is_superuser=True, is_staff=True)
    supplier1 = Supplier.objects.create(identifier=superuser1.username)

    superuser2 = create_random_user(is_superuser=True, is_staff=True)
    supplier2 = Supplier.objects.create(identifier=superuser2.username)

    supplier_provider = "shuup.testing.supplier_provider.UsernameSupplierProvider"
    with override_settings(LANGUAGES=[("en", "en")]):
        with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC=supplier_provider):
            campaign1 = BasketCampaign.objects.create(name="test campaign", active=True, shop=shop, supplier=supplier1)
            campaign2 = BasketCampaign.objects.create(name="test campaign2", active=True, shop=shop, supplier=supplier2)

            view = BasketCampaignListView()
            request = apply_request_middleware(rf.get("/"), user=superuser1, shop=shop)
            assert get_supplier(request) == supplier1
            view.request = request
            assert campaign1 in view.get_queryset()
            assert campaign2 not in view.get_queryset()

            request = apply_request_middleware(rf.get("/"), user=superuser2, shop=shop)
            assert get_supplier(request) == supplier2
            view.request = request
            assert campaign1 not in view.get_queryset()
            assert campaign2 in view.get_queryset()

            # And actual superuser not linked to any supplier can see all like he should
            request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)
            assert get_supplier(request) is None
            view.request = request
            assert campaign1 in view.get_queryset()
            assert campaign2 in view.get_queryset()
