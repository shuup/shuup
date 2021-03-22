# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.db.models import ProtectedError

from shuup.core.models import (
    CustomerTaxGroup,
    Manufacturer,
    PaymentMethod,
    PersonContact,
    Product,
    SalesUnit,
    ShippingMethod,
    Shop,
    ShopProduct,
    Tax,
    TaxClass,
)
from shuup.default_tax.models import TaxRule
from shuup.testing.factories import (
    DEFAULT_NAME,
    create_order_with_product,
    create_product,
    get_default_category,
    get_default_shop,
    get_default_supplier,
    get_test_tax,
)


def get_product():
    shop = get_default_shop()
    product = create_product("tmp", shop, default_price=200)
    return product


@pytest.mark.django_db
def test_manufacturer_removal():
    product = get_product()
    manufacturer = Manufacturer.objects.create(name=DEFAULT_NAME)
    product.manufacturer = manufacturer
    product.save()
    manufacturer.delete()
    product.refresh_from_db()
    assert not product.manufacturer
    assert Product.objects.filter(pk=product.pk).exists()


@pytest.mark.django_db
def test_sales_unit_removal():
    product = get_product()
    sales_unit = SalesUnit.objects.create(name="test", symbol="te")
    product.sales_unit = sales_unit
    product.save()
    with pytest.raises(ProtectedError):
        sales_unit.delete()
    assert Product.objects.filter(pk=product.pk).exists()


@pytest.mark.django_db
def test_tax_class_removal():
    product = get_product()
    tax_class = TaxClass.objects.create(name="test")
    product.tax_class = tax_class
    product.save()
    with pytest.raises(ProtectedError):
        tax_class.delete()
    assert Product.objects.filter(pk=product.pk).exists()


# -------------- CONTACT ----------------
@pytest.mark.django_db
def test_shipping_method_removal():
    tax_class = TaxClass.objects.create(name="test")
    shop = get_default_shop()
    sm = ShippingMethod.objects.create(name="sm", shop=shop, tax_class=tax_class)
    contact = PersonContact.objects.create(name="test", default_shipping_method=sm)
    sm.delete()
    assert PersonContact.objects.filter(pk=contact.pk).exists()


@pytest.mark.django_db
def test_payment_method_removal():
    tax_class = TaxClass.objects.create(name="test")
    shop = get_default_shop()
    pm = PaymentMethod.objects.create(name="sm", shop=shop, tax_class=tax_class)
    contact = PersonContact.objects.create(name="test", default_payment_method=pm)
    pm.delete()
    assert PersonContact.objects.filter(pk=contact.pk).exists()


@pytest.mark.django_db
def test_customer_tax_group_removal():
    ctg = CustomerTaxGroup.objects.create(name="test")
    contact = PersonContact.objects.create(name="test", tax_group=ctg)
    with pytest.raises(ProtectedError):
        ctg.delete()
    assert PersonContact.objects.filter(pk=contact.pk).exists()


# ------------ METHODS ----------------
@pytest.mark.django_db
def test_method_taxclass_removal():
    tax_class = TaxClass.objects.create(name="test")
    shop = get_default_shop()
    pm = PaymentMethod.objects.create(name="test", shop=shop, tax_class=tax_class)
    with pytest.raises(ProtectedError):
        tax_class.delete()
    assert PaymentMethod.objects.filter(pk=pm.id).exists()


# ------------SHOP PRODUCT-------------
@pytest.mark.django_db
def test_shopproduct_primary_category_removal():
    product = get_product()
    category = get_default_category()
    sp = product.get_shop_instance(get_default_shop())
    sp.primary_category = category
    sp.save()
    with pytest.raises(NotImplementedError):
        category.delete()
    assert ShopProduct.objects.filter(pk=sp.pk).exists()


# ------------SHOP -------------
@pytest.mark.django_db
def test_shop_owner_removal():
    contact = PersonContact.objects.create(name="test")
    shop = Shop.objects.create(name="test", public_name="test", owner=contact)
    contact.delete()
    assert Shop.objects.filter(pk=shop.pk).exists()


# -------- TAX ---------------
@pytest.mark.django_db
def test_taxrule_tax_removal():
    tax = Tax.objects.create(rate=1)
    taxrule = TaxRule.objects.create(tax=tax)
    with pytest.raises(ProtectedError):
        tax.delete()
    assert TaxRule.objects.filter(pk=taxrule.pk).exists()


@pytest.mark.django_db
def test_orderlinetax_tax_removal():
    # todo fix
    product = get_product()
    tax_rate = 1
    order = create_order_with_product(
        product=product,
        supplier=get_default_supplier(),
        quantity=1,
        taxless_base_unit_price=10,
        tax_rate=tax_rate,
        shop=get_default_shop(),
    )
    tax = get_test_tax(tax_rate)
    with pytest.raises(ProtectedError):
        tax.delete()
