# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import csv, mock

import pytest
from django.http import HttpResponse
from django.core.cache import cache
from shuup.admin.utils.picotable import PicotableMassAction, PicotableFileMassAction
from shuup.admin.modules.products.mass_actions import InvisibleMassAction, VisibleMassAction

from shuup.core.models import Product, Shop, ShopProduct, ShopStatus, ShopProductVisibility
from shuup.core.utils import context_cache

from shuup.testing.factories import get_default_shop, get_default_supplier, create_product, get_default_currency, get_default_product
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish

class TestPicotableMassAction(PicotableMassAction):

    def process(self, request, ids):
        Product.objects.filter(id__in=ids).update(cost_center="test")


class TestPicotableFileMassAction(PicotableFileMassAction):

    def process(self, request, ids):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        writer = csv.writer(response, delimiter=";")
        writer.writerow(["test", "testing"])
        for product in Product.objects.filter(id__in=ids):
            writer.writerow([product.pk, product.sku])
        return response


@pytest.mark.django_db
def test_mass_actions(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)

    ids = [product.id, product2.id]
    request = apply_request_middleware(rf.get("/"), user=admin_user)

    TestPicotableMassAction().process(request, ids)
    for product in Product.objects.all():
        assert product.cost_center == "test"

    mass_action_response = TestPicotableFileMassAction().process(request, ids)
    assert mass_action_response["Content-disposition"] == 'attachment; filename="products.csv"'


@pytest.mark.django_db
def test_mass_action_cache(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    cache.clear()
    product = create_product(printable_gibberish(), shop=shop, default_price=50)
    product2 = create_product(printable_gibberish(), shop=shop, default_price=100)
    set_bump_cache_for_shop_product = mock.Mock(wraps=context_cache.bump_cache_for_shop_product)
    product_ids = [product.id, product2.id]

    def bump_cache_for_shop_product(shop_product):
        return set_bump_cache_for_shop_product(shop_product)

    with mock.patch.object(context_cache, "bump_cache_for_shop_product", new=bump_cache_for_shop_product):
        assert set_bump_cache_for_shop_product.call_count == 0
        request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)
        InvisibleMassAction().process(request, product_ids)
        # cache is bumped twice because of update_stocks and post_save signal
        assert set_bump_cache_for_shop_product.call_count == 2
        request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)
        VisibleMassAction().process(request, product_ids)
        assert set_bump_cache_for_shop_product.call_count == 4

def create_shop(name):
    return Shop.objects.create(
        name="foobar",
        identifier=name,
        status=ShopStatus.ENABLED,
        public_name=name,
        currency=get_default_currency().code
)

@pytest.mark.django_db
def test_mass_action_multishop(rf, admin_user):
    shop_one = get_default_shop()
    shop_two = create_shop("foobar")
    product = get_default_product()
    shop_product_one = product.get_shop_instance(shop_one)
    shop_product_two = ShopProduct.objects.create(shop=shop_two, product=product)
    shop_product_two.save()
    assert shop_product_one.visibility == ShopProductVisibility.ALWAYS_VISIBLE
    assert shop_product_two.visibility == ShopProductVisibility.ALWAYS_VISIBLE
    request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop_one)
    InvisibleMassAction().process(request, 'all')
    shop_product_one.refresh_from_db()
    shop_product_two.refresh_from_db()
    assert shop_product_one.visibility == ShopProductVisibility.NOT_VISIBLE
    assert shop_product_two.visibility == ShopProductVisibility.ALWAYS_VISIBLE
    request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop_one)
    VisibleMassAction().process(request, 'all')
    shop_product_one.refresh_from_db()
    shop_product_two.refresh_from_db()
    assert shop_product_two.visibility == ShopProductVisibility.ALWAYS_VISIBLE
    assert shop_product_one.visibility == ShopProductVisibility.ALWAYS_VISIBLE
