# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
# test that admin actually saves catalog
import pytest
from django.utils.translation import activate
from shoop.campaigns.admin_module.views import CatalogCampaignEditView, BasketCampaignEditView
from shoop.campaigns.models.campaigns import CatalogCampaign, Coupon
from shoop.testing.factories import get_default_shop, get_default_supplier, create_product
from shoop.testing.utils import apply_request_middleware
from shoop_tests.utils import printable_gibberish
from shoop_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_admin_campaign_edit_view_works(rf, admin_user):
    shop = get_default_shop()
    view_func = CatalogCampaignEditView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    campaign = CatalogCampaign.objects.create(name="test campaign", discount_amount_value="20", active=True, shop=shop)

    response = view_func(request, pk=campaign.pk)
    assert campaign.name in response.rendered_content

    response = view_func(request, pk=None)
    assert response.rendered_content


@pytest.mark.django_db
def test_admin_catalog_campaign_edit_view(rf, admin_user):
    shop = get_default_shop()
    view = CatalogCampaignEditView(request=apply_request_middleware(rf.get("/"), user=admin_user))
    form_class = view.get_form_class()
    form_kwargs = view.get_form_kwargs()
    form = form_class(**form_kwargs)

    assert not form.is_bound

    data = get_form_data(form)
    data.update({
        "shop": shop.pk,
        "name": "test",
    })
    form = form_class(**dict(form_kwargs, data=data))
    form.full_clean()
    assert "You must define discount percentage or amount" in form.errors["__all__"][0]

    data.update({"discount_amount_value": "20"})
    form = form_class(**dict(form_kwargs, data=data))
    form.full_clean()

    # atleast 1 rule is required
    assert "You must set at least one rule for this campaign" in form.errors["__all__"][0]

    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="20")
    data.update({"product_filter": [1]})

    form = form_class(**dict(form_kwargs, data=data))
    form.full_clean()
    assert not form.errors

    campaign = form.save()
    assert campaign.filters.count() == 1


@pytest.mark.django_db
def test_admin_basket_campaign_edit_view(rf, admin_user):
    activate("en")
    shop = get_default_shop()
    view = BasketCampaignEditView(request=apply_request_middleware(rf.get("/"), user=admin_user))
    form_class = view.get_form_class()
    form_kwargs = view.get_form_kwargs()
    form = form_class(**form_kwargs)

    assert not form.is_bound

    data = get_form_data(form)
    data.update({
        "shop": shop.pk,
        "name": "test",
        "public_name__en": "test",
    })
    form = form_class(**dict(form_kwargs, data=data))
    form.full_clean()
    assert "You must define discount percentage or amount" in form.errors["__all__"][0]

    data.update({"discount_amount_value": "20"})
    form = form_class(**dict(form_kwargs, data=data))
    form.full_clean()

    # atleast 1 rule or coupon is required
    assert "You must set atleast one rule or discount code for this campaign." in form.errors["__all__"][0]

    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="20")

    coupon = Coupon.objects.create(code="TEST-CODE", active=True)
    data.update({"coupon": coupon.pk})
    form = form_class(**dict(form_kwargs, data=data))

    form.full_clean()
    assert not form.errors

    campaign = form.save()
    assert campaign.coupon.pk == coupon.pk
