# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.forms import formset_factory

from shuup.admin.modules.products.forms import PackageChildForm, PackageChildFormSet
from shuup.admin.modules.products.utils import clear_existing_package
from shuup.admin.modules.products.views import ProductPackageView
from shuup.core.models import ProductMode, ShopProduct
from shuup.simple_supplier.module import SimpleSupplierModule
from shuup.testing.factories import create_package_product, create_product, get_default_shop, get_supplier
from shuup.testing.utils import apply_all_middleware
from shuup.utils.excs import Problem
from shuup_tests.utils import printable_gibberish
from shuup_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_package_child_formset():
    FormSet = formset_factory(PackageChildForm, PackageChildFormSet, extra=5, can_delete=True)
    parent = create_product(printable_gibberish())
    child = create_product(printable_gibberish())

    # No products in the package
    formset = FormSet(parent_product=parent)
    assert formset.initial_form_count() == 0  # No children yet

    assert not parent.get_all_package_children()

    data = dict(get_form_data(formset, True), **{"form-0-child": child.pk, "form-0-quantity": 2})
    formset = FormSet(parent_product=parent, data=data)
    formset.save()
    assert parent.get_all_package_children()

    clear_existing_package(parent)
    assert not parent.get_all_package_children()


@pytest.mark.django_db
def test_product_not_in_normal_mode():
    FormSet = formset_factory(PackageChildForm, PackageChildFormSet, extra=5, can_delete=True)
    parent = create_product(printable_gibberish())
    child_1 = create_product(printable_gibberish())
    child_1.link_to_parent(parent)
    child_2 = create_product(printable_gibberish())
    parent.verify_mode()

    assert parent.mode == ProductMode.SIMPLE_VARIATION_PARENT

    # Trying to create a package from a non-normal mode product
    with pytest.raises(Problem):
        formset = FormSet(parent_product=parent)
        data = dict(get_form_data(formset, True), **{"form-0-child": child_2.pk, "form-0-quantity": 2})
        formset = FormSet(parent_product=parent, data=data)
        formset.save()


@pytest.mark.django_db
def test_cannot_add_product_to_own_package(rf):
    FormSet = formset_factory(PackageChildForm, PackageChildFormSet, extra=5, can_delete=True)
    parent = create_product(printable_gibberish())

    # No products in the package
    formset = FormSet(parent_product=parent)
    assert formset.initial_form_count() == 0  # No children yet

    assert not parent.get_all_package_children()

    # Try to add a product to its own package
    data = dict(get_form_data(formset, True), **{"form-0-child": parent.pk, "form-0-quantity": 2})
    formset = FormSet(parent_product=parent, data=data)
    formset.save()
    assert not parent.get_all_package_children()


@pytest.mark.parametrize("supplier_enabled", [True, False])
@pytest.mark.django_db
def test_package_edit_view(admin_user, rf, supplier_enabled):
    shop = get_default_shop()
    supplier = get_supplier(SimpleSupplierModule.identifier, shop=shop, stock_managed=True)
    supplier.enabled = supplier_enabled
    supplier.save()
    package = create_package_product(printable_gibberish(), shop, supplier)
    request = apply_all_middleware(rf.get("/"), user=admin_user)
    response = ProductPackageView.as_view()(request=request, pk=package.pk)

    product_ids = []
    for shop_product in ShopProduct.objects.filter(suppliers=supplier, product__mode=ProductMode.NORMAL):
        supplier.adjust_stock(product_id=shop_product.product_id, delta=shop_product.product_id)
        product_ids.append(shop_product.product_id)

    assert response.status_code == 200
    response.render()
    content = response.content.decode("utf-8")

    for product_id in product_ids:
        is_inside = ("Logical count: %s" % product_id) in content
        assert is_inside == supplier_enabled
