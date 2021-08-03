# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from decimal import Decimal
from django.test.utils import override_settings
from django.utils.text import slugify

from shuup.admin.modules.suppliers.views import SupplierDeleteView, SupplierEditView, SupplierListView
from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.core.models import Supplier, SupplierType
from shuup.testing import factories
from shuup.testing.factories import get_default_supplier
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse


@pytest.mark.django_db
def test_suppliers_list(rf, admin_user):
    shop = factories.get_default_shop()
    shop2 = factories.get_shop(identifier="shop2")

    supplier1 = Supplier.objects.create(name="supplier1")
    supplier2 = Supplier.objects.create(name="supplier1")
    supplier3 = Supplier.objects.create(name="supplier1")
    # only supplier 1 has shop
    supplier1.shops.add(shop)
    supplier3.shops.add(shop2)

    list_view = SupplierListView.as_view()

    staff_user = factories.create_random_user("en", is_staff=True)
    shop.staff_members.add(staff_user)

    for user in [admin_user, staff_user]:
        request = apply_request_middleware(rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=user)
        response = list_view(request)
        data = json.loads(response.content.decode("utf-8"))
        ids = [sup["_id"] for sup in data["items"]]
        assert supplier1.id in ids
        assert supplier2.id in ids


@pytest.mark.django_db
@pytest.mark.parametrize("manage_stock", [True, False])
@pytest.mark.parametrize("stock_module", [[], [1]])
def test_suppliers_edit(rf, admin_user, manage_stock, stock_module):
    shop = factories.get_default_shop()
    edit_view = SupplierEditView.as_view()

    staff_user = factories.create_random_user("en", is_staff=True)
    shop.staff_members.add(staff_user)

    with override_settings(SHUUP_ENABLE_MULTIPLE_SUPPLIERS=True):
        for index, user in enumerate([admin_user, staff_user]):
            payload = {
                "base-name": "Supplier Name %d" % index,
                "base-description__en": "Supplier Description %d" % index,
                "base-type": SupplierType.INTERNAL.value,
                "base-stock_managed": manage_stock,
                "base-supplier_modules": stock_module,
                "base-shops": shop.pk,
                "base-enabled": "on",
                "base-logo": "",
                "address-name": "Address Name %d" % index,
                "address-email": "email@example.com",
                "address-phone": "23742578329",
                "address-tax_number": "ABC123",
                "address-street": "Streetz",
                "address-postal_code": "90014",
                "address-city": "Los Angeles",
                "address-region_code": "CA",
                "address-country": "US",
            }
            if manage_stock and not stock_module:
                request = apply_request_middleware(rf.post("/", payload), user=user)
                response = edit_view(request)
                response.render()
                assert bool(
                    "It is not possible to manage inventory when no module is selected." in response.content.decode()
                )
                assert response.status_code == 200
            else:
                request = apply_request_middleware(rf.post("/", payload), user=user)
                response = edit_view(request)
                assert response.status_code == 302

                supplier = Supplier.objects.last()
                assert response.url == reverse("shuup_admin:supplier.edit", kwargs=dict(pk=supplier.pk))
                assert supplier.name == payload["base-name"]
                assert supplier.slug == slugify(supplier.name)
                assert supplier.description == payload["base-description__en"]
                assert supplier.shops.count() == 1
                assert supplier.enabled
                assert supplier.contact_address.name == payload["address-name"]

                request = apply_request_middleware(rf.get("/"), user=user)
                response = edit_view(request, **{"pk": supplier.pk})
                assert response.status_code == 200


@pytest.mark.django_db
def test_supplier_create(rf, admin_user):
    shop = factories.get_default_shop()
    edit_view = SupplierEditView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = edit_view(request, **{"pk": None})
    assert response.status_code == 200


@pytest.mark.django_db
def test_suppliers_delete(rf, admin_user):
    delete_view = SupplierDeleteView.as_view()

    supplier = get_default_supplier()
    request_admin = apply_request_middleware(rf.post("/"), user=admin_user)
    response = delete_view(request_admin, **{"pk": supplier.pk})
    assert response.status_code == 302
    assert response.url == reverse("shuup_admin:supplier.list")
    assert Supplier.objects.filter(pk=supplier.pk).not_deleted().exists() is False

    supplier.deleted = False
    supplier.save()

    request_supplier = apply_request_middleware(rf.post("/"), user=admin_user)
    with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC="shuup.testing.supplier_provider.FirstSupplierProvider"):
        response = delete_view(request_supplier, **{"pk": supplier.pk})
        assert response.status_code == 302
        assert response.url == reverse("shuup_admin:supplier.list")
        assert Supplier.objects.filter(pk=supplier.pk).not_deleted().exists() is False


@pytest.mark.django_db
def test_suppliers_ensure_deleted_inlist(rf, admin_user):
    supplier = get_default_supplier()

    list_view = SupplierListView.as_view()
    request = apply_request_middleware(rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user)

    response = list_view(request)
    data = json.loads(response.content.decode("utf-8"))
    assert data["pagination"]["nItems"] == 1

    supplier.soft_delete()
    response = list_view(request)
    data = json.loads(response.content.decode("utf-8"))
    assert data["pagination"]["nItems"] == 0


@pytest.mark.django_db
def test_supplier_changed_reindex_catalog(rf, admin_user):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier(shop)
    supplier.stock_managed = True
    supplier.save()
    product = factories.create_product("p1", shop, supplier, default_price=Decimal("10"))
    supplier.adjust_stock(product.pk, 40)  # add 40 to the stock
    ProductCatalog.index_product(product)

    catalog = ProductCatalog(ProductCatalogContext(purchasable_only=True))
    assert product in catalog.get_products_queryset()

    # disable the supplier
    edit_view = SupplierEditView.as_view()
    payload = {
        "base-name": supplier.name,
        "base-description__en": "",
        "base-type": SupplierType.INTERNAL.value,
        "base-stock_managed": True,
        "base-supplier_modules": [supplier.supplier_modules.first().pk],
        "base-shops": shop.pk,
        "base-enabled": "",
        "base-logo": "",
        "address-name": "Address Name",
        "address-email": "email@example.com",
        "address-phone": "23742578329",
        "address-tax_number": "ABC123",
        "address-street": "Streetz",
        "address-postal_code": "90014",
        "address-city": "Los Angeles",
        "address-region_code": "CA",
        "address-country": "US",
    }
    request = apply_request_middleware(rf.post("/", payload), user=admin_user)
    response = edit_view(request, pk=supplier.pk)
    assert response.status_code == 302

    supplier.refresh_from_db()
    assert not supplier.enabled

    # product is not available anymore
    assert product not in catalog.get_products_queryset()
