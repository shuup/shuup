# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import mock
import pytest
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import activate

from shuup.admin.modules.products.mass_actions import ExportProductsCSVAction, InvisibleMassAction, VisibleMassAction
from shuup.admin.utils.picotable import PicotableMassAction
from shuup.core.models import Shop, ShopProduct, ShopProductVisibility, ShopStatus
from shuup.core.utils import context_cache
from shuup.testing.factories import (
    create_product,
    get_default_currency,
    get_default_product,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.importing import load
from shuup_tests.utils import printable_gibberish


class TestPicotableMassAction(PicotableMassAction):
    def process(self, request, ids):
        ShopProduct.objects.filter(id__in=ids).update(purchasable=False)


@pytest.mark.django_db
def test_mass_actions(rf, admin_user):
    activate("en")
    shop = get_default_shop()
    supplier = get_default_supplier()
    product1 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)

    shop_product1 = product1.get_shop_instance(shop)
    shop_product2 = product2.get_shop_instance(shop)

    ids = [shop_product1.id, shop_product2.id]
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    TestPicotableMassAction().process(request, ids)

    for shop_product in ShopProduct.objects.all():
        assert shop_product.purchasable is False

    mass_action_response = ExportProductsCSVAction().process(request, ids)
    assert mass_action_response["Content-disposition"] == 'attachment; filename="products.csv"'


@pytest.mark.django_db
def test_mass_actions_product_ids_mixup(rf, admin_user):
    shop = get_default_shop()
    get_default_supplier()
    product1 = create_product("sku1")
    product2 = create_product("sku2")

    with pytest.raises(ObjectDoesNotExist):
        product1.get_shop_instance(shop)
        product2.get_shop_instance(shop)

    # Let's create shop products in different order so product and shop product
    # ids does not match.
    default_price = shop.create_price(10)
    ShopProduct.objects.create(
        product=product2,
        shop=shop,
        default_price=default_price,
        visibility=ShopProductVisibility.ALWAYS_VISIBLE,
        name="SKU 1 product",
    )
    ShopProduct.objects.create(
        product=product1,
        shop=shop,
        default_price=default_price,
        visibility=ShopProductVisibility.ALWAYS_VISIBLE,
        name="SKU 1 product",
    )

    shop_product1 = product1.get_shop_instance(shop)
    shop_product2 = product2.get_shop_instance(shop)
    assert shop_product1.pk != product1.pk
    assert shop_product2.pk != product2.pk

    view = load("shuup.admin.modules.products.views:ProductListView").as_view()
    request = apply_request_middleware(rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user)
    response = view(request)
    assert 200 <= response.status_code < 300
    data = json.loads(response.content.decode("utf-8"))

    shop_product1_id = [item["_id"] for item in data["items"] if item["product_sku"] == "sku1"][0]
    assert shop_product1_id == shop_product1.pk
    InvisibleMassAction().process(request, [shop_product1_id])
    shop_product1.refresh_from_db()
    assert shop_product1.visibility == ShopProductVisibility.NOT_VISIBLE


@pytest.mark.django_db
def test_mass_action_cache(rf, admin_user):
    shop = get_default_shop()
    cache.clear()
    product = create_product(printable_gibberish(), shop=shop, default_price=50)
    product2 = create_product(printable_gibberish(), shop=shop, default_price=100)

    shop_product = product.get_shop_instance(shop)
    shop_product2 = product2.get_shop_instance(shop)

    set_bump_cache_for_shop_product = mock.Mock(wraps=context_cache.bump_cache_for_shop_product)

    def bump_cache_for_shop_product(item):
        return set_bump_cache_for_shop_product(item)

    request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)

    with mock.patch.object(context_cache, "bump_cache_for_shop_product", new=bump_cache_for_shop_product):
        assert set_bump_cache_for_shop_product.call_count == 0
        InvisibleMassAction().process(request, [shop_product.id, shop_product2.id])
        assert set_bump_cache_for_shop_product.call_count == 2

        VisibleMassAction().process(request, [shop_product.id, shop_product2.id])
        assert set_bump_cache_for_shop_product.call_count == 4


@pytest.mark.django_db
def test_mass_action_multishop(rf, admin_user):
    def create_shop(name):
        return Shop.objects.create(
            name="foobar",
            identifier=name,
            status=ShopStatus.ENABLED,
            public_name=name,
            currency=get_default_currency().code,
        )

    shop_one = get_default_shop()
    shop_two = create_shop("foobar")
    product = get_default_product()
    shop_product_one = product.get_shop_instance(shop_one)
    shop_product_two = ShopProduct.objects.create(shop=shop_two, product=product)
    shop_product_two.save()
    assert shop_product_one.visibility == ShopProductVisibility.ALWAYS_VISIBLE
    assert shop_product_two.visibility == ShopProductVisibility.ALWAYS_VISIBLE
    request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop_one)
    InvisibleMassAction().process(request, "all")
    shop_product_one.refresh_from_db()
    shop_product_two.refresh_from_db()
    assert shop_product_one.visibility == ShopProductVisibility.NOT_VISIBLE
    assert shop_product_two.visibility == ShopProductVisibility.ALWAYS_VISIBLE
    request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop_one)
    VisibleMassAction().process(request, "all")
    shop_product_one.refresh_from_db()
    shop_product_two.refresh_from_db()
    assert shop_product_two.visibility == ShopProductVisibility.ALWAYS_VISIBLE
    assert shop_product_one.visibility == ShopProductVisibility.ALWAYS_VISIBLE
