# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as PermissionGroup
from django.db.models import Model

from shuup.apps.provides import get_provide_objects, override_provides
from shuup.campaigns.models.campaigns import Coupon
from shuup.core.models import (
    Attribute,
    AttributeType,
    Carrier,
    Category,
    CustomCarrier,
    CustomerTaxGroup,
    Manufacturer,
    PaymentMethod,
    Product,
    ProductType,
    ShippingMethod,
    Shop,
    Supplier,
    Tax,
    TaxClass,
)
from shuup.discounts.models import Discount
from shuup.testing.factories import (
    create_product,
    create_random_user,
    get_default_category,
    get_default_permission_group,
    get_default_product_type,
    get_default_shop,
    get_default_supplier,
    get_default_tax_class,
)
from shuup.xtheme.models import Font

User = get_user_model()


def get_model_selector(model):
    if not isinstance(model, type) or not issubclass(model, Model):
        return None
    return "%s.%s" % (model._meta.app_label, model._meta.model_name)


def get_object_selector_results(model, shop, user, search_term, supplier=None, **kwargs):
    selector = get_model_selector(model)
    if not selector:
        selector = model

    for admin_object_selector_class in sorted(
        get_provide_objects("admin_object_selector"), key=lambda provides: provides.ordering
    ):
        if not admin_object_selector_class.handles_selector(selector):
            continue
        admin_object_selector = admin_object_selector_class(model, shop=shop, user=user, supplier=supplier)

        if not admin_object_selector.has_permission():
            return None

        return admin_object_selector.get_objects(search_term, **kwargs)


@pytest.mark.django_db
def test_product_selector(admin_user):

    shop = get_default_shop()
    product_name_en = "The Product"
    product = create_product("the product", shop=shop, **{"name": product_name_en})
    product.get_shop_instance(shop)
    assert get_object_selector_results(Product, shop, admin_user, "product")


@pytest.mark.django_db
def test_manufacturer_selector(admin_user):

    shop = get_default_shop()
    Manufacturer.objects.create(name="test")
    assert get_object_selector_results(Manufacturer, shop, admin_user, "test")


@pytest.mark.django_db
def test_discount_selector(admin_user):
    shop = get_default_shop()
    Discount.objects.create(name="test", shop=shop)
    assert get_object_selector_results(Discount, shop, admin_user, "test")


@pytest.mark.django_db
def test_coupon_selector(admin_user):
    shop = get_default_shop()
    Coupon.objects.create(code="test", shop=None, active=True)
    assert get_object_selector_results(Coupon, shop, admin_user, "test") == []
    Coupon.objects.create(code="test", shop=shop)
    assert get_object_selector_results(Coupon, shop, admin_user, "test") == []
    Coupon.objects.create(code="test", shop=shop, active=True)
    assert get_object_selector_results(Coupon, shop, admin_user, "test")


@pytest.mark.django_db
def test_attribute_selector(admin_user):
    shop = get_default_shop()
    Attribute.objects.create(type=AttributeType.INTEGER, identifier="test-1", name="Test attribute")
    assert get_object_selector_results(Attribute, shop, admin_user, "test attribute")


@pytest.mark.django_db
def test_attribute_selector(admin_user):
    shop = get_default_shop()
    Attribute.objects.create(type=AttributeType.INTEGER, identifier="test-1", name="Test attribute")
    assert get_object_selector_results(Attribute, shop, admin_user, "test attribute")


@pytest.mark.django_db
def test_category_selector(admin_user):
    shop = get_default_shop()
    get_default_category()
    assert get_object_selector_results(Category, shop, admin_user, "default")


@pytest.mark.django_db
def test_permission_groups_selector(admin_user):
    shop = get_default_shop()
    get_default_permission_group()
    assert get_object_selector_results(PermissionGroup, shop, admin_user, "default")


@pytest.mark.django_db
def test_product_type_selector(admin_user):
    shop = get_default_shop()
    get_default_product_type()
    assert get_object_selector_results(ProductType, shop, admin_user, "default")


@pytest.mark.django_db
def test_carrier_selector(admin_user):
    shop = get_default_shop()
    carrier = Carrier.objects.create(name="Carrier1")
    carrier.shops.add(shop.pk)
    assert get_object_selector_results(Carrier, shop, admin_user, "Carrier1")

    custom_carrier = CustomCarrier.objects.create(name="CustomCarrier1")
    custom_carrier.shops.add(shop.pk)
    assert get_object_selector_results(CustomCarrier, shop, admin_user, "CustomCarrier")


@pytest.mark.django_db
def test_payment_method_selector(admin_user):
    tax_class = TaxClass.objects.create(name="test class")
    shop = get_default_shop()
    PaymentMethod.objects.create(name="payment method", shop=shop, tax_class=tax_class)

    assert get_object_selector_results(PaymentMethod, shop, admin_user, "payment")


@pytest.mark.django_db
def test_shipping_method_selector(admin_user):
    tax_class = TaxClass.objects.create(name="test class")
    shop = get_default_shop()
    ShippingMethod.objects.create(name="shipping method", shop=shop, tax_class=tax_class)

    assert get_object_selector_results(ShippingMethod, shop, admin_user, "shipping")


@pytest.mark.django_db
def test_shop_selector(admin_user):
    shop = get_default_shop()

    assert get_object_selector_results(Shop, shop, admin_user, "Default")


@pytest.mark.django_db
def test_supplier_selector(admin_user):
    shop = get_default_shop()
    get_default_supplier()
    assert get_object_selector_results(Supplier, shop, admin_user, "Default")


@pytest.mark.django_db
def test_tax_selector(admin_user):
    shop = get_default_shop()
    tax = Tax.objects.create(code="any", rate=0.1, name="Tax for any customer", enabled=False)
    assert get_object_selector_results(Tax, shop, admin_user, "Tax") == []
    tax.enabled = True
    tax.save()
    assert get_object_selector_results(Tax, shop, admin_user, "Tax")


@pytest.mark.django_db
def test_tax_class_selector(admin_user):
    shop = get_default_shop()
    get_default_tax_class()
    assert get_object_selector_results(TaxClass, shop, admin_user, "Default")


@pytest.mark.django_db
def test_customer_tax_group_selector(admin_user):
    shop = get_default_shop()
    CustomerTaxGroup.objects.create(name="test")
    assert get_object_selector_results(CustomerTaxGroup, shop, admin_user, "test")


@pytest.mark.django_db
def test_user_selector(admin_user):
    shop = get_default_shop()
    u = create_random_user()
    assert get_object_selector_results(User, shop, admin_user, u.first_name)


@pytest.mark.django_db
def test_font_selector(admin_user):
    shop = get_default_shop()
    font = Font.objects.create(name="font", shop=shop)
    assert get_object_selector_results(Font, shop, admin_user, "font")


@pytest.mark.django_db
def test_generic_selector(admin_user):
    shop = get_default_shop()

    with override_provides(
        "admin_object_selector",
        [
            "shuup.admin.modules.attributes.object_selector.AttributeAdminObjectSelector",
            "shuup.admin.modules.categories.object_selector.CategoryAdminObjectSelector",
            "shuup.admin.modules.contacts.object_selector.ContactAdminObjectSelector",
            "shuup.admin.modules.contacts.object_selector.PersonContactAdminObjectSelector",
            "shuup.admin.modules.contacts.object_selector.CompanyContactAdminObjectSelector",
            "shuup.admin.modules.manufacturers.object_selector.ManufacturerAdminObjectSelector",
            "shuup.admin.modules.permission_groups.object_selector.PermissionGroupAdminObjectSelector",
            "shuup.admin.modules.product_types.object_selector.ProductTypeAdminObjectSelector",
            "shuup.admin.modules.products.object_selector.ProductAdminObjectSelector",
            "shuup.admin.modules.products.object_selector.ShopProductAdminObjectSelector",
            "shuup.admin.modules.services.object_selector.CarrierAdminObjectSelector",
            "shuup.admin.modules.services.object_selector.PaymentMethodAdminObjectSelector",
            "shuup.admin.modules.services.object_selector.ShippingMethodAdminObjectSelector",
            "shuup.admin.modules.shops.object_selector.ShopAdminObjectSelector",
            "shuup.admin.modules.suppliers.object_selector.SupplierAdminObjectSelector",
            "shuup.admin.modules.taxes.object_selector.CustomerTaxGroupAdminObjectSelector",
            "shuup.admin.modules.taxes.object_selector.TaxAdminObjectSelector",
            "shuup.admin.modules.taxes.object_selector.TaxClassAdminObjectSelector",
            "shuup.admin.modules.users.object_selector.UserAdminObjectSelector",
            "shuup.campaigns.admin_module.object_selector.CouponAdminObjectSelector",
            "shuup.discounts.admin.object_selector.DiscountAdminObjectSelector",
            "shuup.testing.modules.mocker.object_selector.MockAdminObjectSelector",
        ],
    ):
        assert get_object_selector_results("shuup.mock", shop, admin_user, "search")
