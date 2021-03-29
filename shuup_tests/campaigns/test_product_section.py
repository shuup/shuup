# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test import override_settings

from shuup.admin.supplier_provider import get_supplier
from shuup.campaigns.admin_module.sections import ProductCampaignsSection
from shuup.campaigns.models.basket_conditions import ProductsInBasketCondition
from shuup.campaigns.models.basket_effects import BasketDiscountAmount
from shuup.campaigns.models.campaigns import BasketCampaign
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup_tests.campaigns import initialize_test


@pytest.mark.django_db
def test_product_campaigns_section_no_shop_product(rf, admin_user):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    request.shop = shop
    context = ProductCampaignsSection.get_context_data(factories.create_product("test1"), request)
    assert not context
    context = ProductCampaignsSection.get_context_data(factories.create_product("test2", shop=shop), request)
    assert context[shop]["basket_campaigns"].count() == 0


@pytest.mark.django_db
def test_product_campaigns_section(rf, admin_user):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()

    product = factories.create_product("test", shop=shop, supplier=supplier, default_price=10)
    campaign1 = _create_active_campaign(shop, supplier, product)
    campaign2 = _create_active_campaign(shop, None, product)

    shop_staff_user = factories.create_random_user(is_staff=True)
    shop.staff_members.add(shop_staff_user)

    supplier_staff_user = factories.create_random_user(username=supplier.identifier, is_staff=True)
    shop.staff_members.add(supplier_staff_user)

    supplier_provider = "shuup.testing.supplier_provider.UsernameSupplierProvider"
    with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC=supplier_provider):
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        request.shop = shop
        assert get_supplier(request) is None
        context = ProductCampaignsSection.get_context_data(product, request)
        assert context[shop]["basket_campaigns"].count() == 2

        request = apply_request_middleware(rf.get("/"), user=shop_staff_user)
        request.shop = shop
        assert get_supplier(request) is None
        context = ProductCampaignsSection.get_context_data(product, request)
        assert context[shop]["basket_campaigns"].count() == 2

        request = apply_request_middleware(rf.get("/"), user=supplier_staff_user)
        request.shop = shop
        assert get_supplier(request) == supplier
        context = ProductCampaignsSection.get_context_data(product, request)
        assert context[shop]["basket_campaigns"].count() == 1

        campaign1.supplier = None
        campaign1.save()

        context = ProductCampaignsSection.get_context_data(product, request)
        assert context[shop]["basket_campaigns"].count() == 0

        BasketCampaign.objects.update(supplier=supplier)

        context = ProductCampaignsSection.get_context_data(product, request)
        assert context[shop]["basket_campaigns"].count() == 2


def _create_active_campaign(shop, supplier, product):
    basket_rule = ProductsInBasketCondition.objects.create(quantity=2)
    basket_rule.products.add(product)
    campaign = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", active=True, supplier=supplier)
    campaign.conditions.add(basket_rule)
    campaign.save()
    BasketDiscountAmount.objects.create(campaign=campaign, discount_amount=5)
    return campaign
