# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.campaigns.models import CatalogCampaign, CatalogFilterCachedShopProduct, ProductFilter
from shuup.campaigns.models.matching import get_matching_catalog_filters
from shuup.testing.factories import create_product, get_default_supplier
from shuup_tests.campaigns import initialize_test
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_filter_caching(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price
    product_price = "100"
    discount_percentage = "0.30"

    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=product_price)
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=product_price)

    assert product.pk != product2.pk  # ensure they're different

    # create catalog campaign
    catalog_filter = ProductFilter.objects.create()
    catalog_filter.products.add(product)

    catalog_campaign = CatalogCampaign.objects.create(shop=shop, active=True, name="test")
    catalog_campaign.filters.add(catalog_filter)
    assert CatalogFilterCachedShopProduct.objects.count() == 1
    catalog_campaign.save()
    assert CatalogFilterCachedShopProduct.objects.count() == 1

    entry = CatalogFilterCachedShopProduct.objects.first()
    assert entry.pk == get_matching_catalog_filters(product.get_shop_instance(shop))[0]

    # create another campaign
    catalog_filter2 = ProductFilter.objects.create()
    catalog_filter2.products.add(product2)
    catalog_campaign2 = CatalogCampaign.objects.create(shop=shop, active=True, name="test")
    catalog_campaign2.filters.add(catalog_filter2)
    assert CatalogFilterCachedShopProduct.objects.count() == 2
    catalog_campaign2.save()
    assert CatalogFilterCachedShopProduct.objects.count() == 2  # new cache for this product was created

    entry = CatalogFilterCachedShopProduct.objects.last()
    assert entry.pk == get_matching_catalog_filters(product2.get_shop_instance(shop))[0]

    # third campaign
    catalog_filter3 = ProductFilter.objects.create()
    catalog_filter3.products.add(product2)
    catalog_campaign3 = CatalogCampaign.objects.create(shop=shop, active=True, name="test")
    catalog_campaign3.filters.add(catalog_filter3)
    assert CatalogFilterCachedShopProduct.objects.count() == 3
    catalog_campaign3.save()
    assert CatalogFilterCachedShopProduct.objects.count() == 3  # new one for this filter again

    expected = get_matching_catalog_filters(product2.get_shop_instance(shop))
    for id in expected:
        assert id in [catalog_filter2.pk, catalog_filter3.pk]
