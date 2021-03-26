# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from django.http.response import Http404
from django.test import override_settings
from filer.models import File

from shuup.admin.module_registry import replace_modules
from shuup.admin.modules.categories import CategoryModule
from shuup.admin.modules.manufacturers import ManufacturerModule
from shuup.admin.modules.media import MediaModule
from shuup.admin.modules.product_types import ProductTypeModule
from shuup.admin.modules.products import ProductModule
from shuup.admin.modules.products.views import (
    ProductDeleteView,
    ProductEditView,
    ProductListView,
    ProductMediaBulkAdderView,
)
from shuup.admin.modules.services import PaymentMethodModule, ShippingMethodModule
from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.urls import get_model_url
from shuup.admin.views.search import get_search_results
from shuup.core.models import Product, ProductMedia, ProductMediaKind, ProductVisibility, ShopProduct
from shuup.importer.admin_module import ImportAdminModule
from shuup.testing.factories import (
    create_product,
    create_random_user,
    get_default_product,
    get_default_shop,
    get_default_supplier,
    get_shop as create_shop,
    get_shop as get_new_shop,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.admin.utils import admin_only_urls
from shuup_tests.utils import empty_iterable


@pytest.mark.django_db
def test_product_module_search(rf, admin_user):
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)

    with replace_modules(
        [
            CategoryModule,
            ImportAdminModule,
            ProductModule,
            MediaModule,
            ProductTypeModule,
            ManufacturerModule,
            PaymentMethodModule,
            ShippingMethodModule,
        ]
    ):
        with admin_only_urls():
            default_product = get_default_product()
            model_url = get_model_url(default_product, shop=get_shop(request))
            sku = default_product.sku
            assert any(sr.url == model_url for sr in get_search_results(request, query=sku))  # Queries work
            assert any(sr.is_action for sr in get_search_results(request, query=sku[:5]))  # Actions work
            assert empty_iterable(get_search_results(request, query=sku[:2]))  # Short queries don't


@pytest.mark.django_db
def test_product_edit_view_works_at_all(rf, admin_user):
    shop = get_default_shop()
    product = create_product("test-product", shop, default_price=200)
    shop_product = product.get_shop_instance(shop)
    shop_product.visibility_limit = ProductVisibility.VISIBLE_TO_GROUPS
    shop_product.save()
    request = apply_request_middleware(rf.get("/"), user=admin_user)

    with replace_modules(
        [
            CategoryModule,
            ImportAdminModule,
            ProductModule,
            MediaModule,
            ProductTypeModule,
            ManufacturerModule,
            PaymentMethodModule,
            ShippingMethodModule,
        ]
    ):
        with admin_only_urls():
            view_func = ProductEditView.as_view()
            response = view_func(request, pk=shop_product.pk)
            response.render()
            assert product.sku in response.rendered_content  # it's probable the SKU is there
            response = view_func(request, pk=None)  # "new mode"
            assert response.rendered_content  # yeah, something gets rendered


@pytest.mark.django_db
def test_product_edit_view_with_params(rf, admin_user):
    get_default_shop()
    sku = "test-sku"
    name = "test name"
    request = apply_request_middleware(rf.get("/", {"name": name, "sku": sku}), user=admin_user)

    with replace_modules(
        [
            CategoryModule,
            ImportAdminModule,
            ProductModule,
            MediaModule,
            ProductTypeModule,
            ManufacturerModule,
            PaymentMethodModule,
            ShippingMethodModule,
        ]
    ):
        with admin_only_urls():
            view_func = ProductEditView.as_view()
            response = view_func(request)
            assert sku in response.rendered_content  # it's probable the SKU is there
            assert name in response.rendered_content  # it's probable the name is there


@pytest.mark.django_db
def test_product_delete_view(rf, admin_user):
    shop = get_default_shop()
    prod = create_product("prod")
    shop_product = ShopProduct.objects.create(product=prod, shop=shop)
    shop_product.save()
    assert shop_product.pk != shop_product.product.pk
    request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
    view_func = ProductDeleteView.as_view()
    response = view_func(request, pk=shop_product.pk)
    prod.refresh_from_db()
    assert prod.deleted


@pytest.mark.django_db
def test_product_media_bulk_adder(rf, admin_user):
    shop = get_default_shop()
    product = create_product("test-product", shop)
    f = File.objects.create(name="test")
    f2 = File.objects.create(name="test2")
    assert not ProductMedia.objects.count()

    shop_product = product.get_shop_instance(shop)

    view_func = ProductMediaBulkAdderView.as_view()
    # bad request - no params
    request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
    response = view_func(request, pk=shop_product.pk)
    assert response.status_code == 400
    assert not ProductMedia.objects.count()
    # bad request - invalid shop
    request = apply_request_middleware(
        rf.post("/", {"shop_id": 0, "file_ids": [f.id], "kind": "media"}), user=admin_user, shop=shop
    )
    response = view_func(request, pk=shop_product.pk)
    assert response.status_code == 400
    assert not ProductMedia.objects.count()
    # bad request - invalid product
    request = apply_request_middleware(rf.post("/", {"file_ids": [f.id], "kind": "media"}), user=admin_user, shop=shop)
    response = view_func(request, pk=100)
    assert response.status_code == 400
    assert not ProductMedia.objects.count()
    # bad request - invalid kind
    request = apply_request_middleware(rf.post("/", {"file_ids": [f.id], "kind": "test"}), user=admin_user, shop=shop)
    response = view_func(request, pk=shop_product.pk)
    assert response.status_code == 400
    assert not ProductMedia.objects.count()
    # bad request - invalid file
    request = apply_request_middleware(rf.post("/", {"file_ids": [0], "kind": "media"}), user=admin_user, shop=shop)
    response = view_func(request, pk=shop_product.pk)
    assert response.status_code == 400
    assert not ProductMedia.objects.count()
    # bad request - empty file array
    request = apply_request_middleware(rf.post("/", {"file_ids": [], "kind": "media"}), user=admin_user, shop=shop)
    response = view_func(request, pk=shop_product.pk)
    assert response.status_code == 400
    assert not ProductMedia.objects.count()
    # add one file
    request = apply_request_middleware(rf.post("/", {"file_ids": [f.id], "kind": "media"}), user=admin_user, shop=shop)
    response = view_func(request, pk=shop_product.pk)
    assert response.status_code == 200
    assert ProductMedia.objects.filter(product_id=product.pk, file_id=f.id, kind=ProductMediaKind.GENERIC_FILE).exists()
    # add two files but one already exists
    request = apply_request_middleware(
        rf.post("/", {"file_ids": [f.id, f2.id], "kind": "media"}), user=admin_user, shop=shop
    )
    response = view_func(request, pk=shop_product.pk)
    assert response.status_code == 200
    assert ProductMedia.objects.count() == 2
    assert ProductMedia.objects.filter(
        product_id=product.pk, file_id=f2.id, kind=ProductMediaKind.GENERIC_FILE
    ).exists()


@pytest.mark.django_db
def test_product_edit_view_multipleshops(rf):
    """
    Check whether a staff user from Shop A can see the product from Shop B
    when the staff user is only attached to Shop A
    """
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        assert Product.objects.count() == 0
        shop1 = get_default_shop()
        shop2 = get_new_shop(identifier="shop2", domain="shop2", name="Shop 2")
        shop2_staff = create_random_user(is_staff=True)
        shop2.staff_members.add(shop2_staff)

        assert Product.objects.count() == 1

        product = create_product("shop1-product", shop=shop1)
        assert Product.objects.count() == 2
        # Default product is set to default shop as well
        assert ShopProduct.objects.filter(shop=shop1).count() == 2

        # Default product created in get_new_shop-function
        assert ShopProduct.objects.filter(shop=shop2).count() == 1
        shop_product = product.get_shop_instance(shop1)
        request = apply_request_middleware(rf.get("/", HTTP_HOST=shop2.domain), user=shop2_staff)
        assert get_shop(request) == shop2

        view_func = ProductEditView.as_view()
        with pytest.raises(Http404):
            view_func(request, pk=shop_product.pk)

        view_func = ProductListView.as_view()
        payload = {"jq": json.dumps({"perPage": 100, "page": 1}), "shop": shop2.pk}
        request = apply_request_middleware(rf.get("/", payload, HTTP_HOST=shop2.domain), user=shop2_staff)
        assert get_shop(request) == shop2

        response = view_func(request)
        assert response.status_code == 200
        data = json.loads(response.content.decode("utf-8"))
        assert len(data["items"]) == 1  # There is one shop product create in "get new shop"


@pytest.mark.django_db
def test_product_edit_view_multiplessuppliers(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("product", shop=shop)
    shop_product = product.get_shop_instance(shop)

    product_with_supplier = create_product(sku="product_with_supplier", shop=shop, supplier=supplier)
    shop_product_with_supplier = product_with_supplier.get_shop_instance(shop)

    with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC="shuup.testing.supplier_provider.FirstSupplierProvider"):
        request = apply_request_middleware(rf.get("/", HTTP_HOST=shop.domain), user=admin_user)
        view_func = ProductEditView.as_view()
        with pytest.raises(Http404):
            view_func(request, pk=shop_product.pk)
        view_func(request, pk=shop_product_with_supplier.pk)


@pytest.mark.django_db
def test_product_module_get_model_url(rf, admin_user):
    shop1 = create_shop(identifier="shop1", enabled=True)
    shop2 = create_shop(identifier="shop2", enabled=True)

    product = create_product("product1", shop=shop1)

    module = ProductModule()

    assert module.get_model_url(product, "edit")
    assert module.get_model_url(product, "edit", shop1)
    assert module.get_model_url(product, "edit", shop2) is None

    ShopProduct.objects.create(shop=shop2, product=product)
    assert module.get_model_url(product, "edit", shop2)
