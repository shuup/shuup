from datetime import timedelta, datetime

import pytest
from django.utils.translation import activate
from shuup.category_extensions.models.category_populator import CategoryPopulator
from shuup.category_extensions.models.populator_rules import CreationDatePopulatorRule, ManufacturerPopulatorRule, \
    AttributePopulatorRule
from shuup.core.models import Attribute
from shuup.core.models import AttributeType
from shuup.core.models import Manufacturer
from shuup.core.models import ProductAttribute
from shuup.testing.factories import CategoryFactory, get_default_shop, create_product, get_default_supplier
from shuup.utils.enums import ComparisonOperator

@pytest.skip  # skip for now, enable again when signals are in use, these should pass then

@pytest.mark.django_db
def test_category_populates_with_dates(rf):
    shop = get_default_shop()
    category = CategoryFactory()
    supplier = get_default_supplier()
    auto_category = CategoryFactory()

    past = datetime.now() - timedelta(days=2)
    future = datetime.now() + timedelta(days=2)
    poprule = CreationDatePopulatorRule.objects.create(
        start_date=past, end_date=future)

    populator = CategoryPopulator.objects.create(category=auto_category)
    populator.rules.add(poprule)

    product = create_product("test-sku", shop=shop, supplier=supplier, default_price=100)
    shop_product = product.get_shop_instance(shop)

    assert shop_product.categories.filter(pk=auto_category.pk).exists()

    product.created_on = past - timedelta(days=2)  # make product to past
    product.save()

    # clear unmatching
    populator.clear_unmatching()

    assert not shop_product.categories.filter(pk=auto_category.pk).exists()


@pytest.mark.django_db
def test_category_populates_with_manufacturer(rf):
    shop = get_default_shop()
    supplier = get_default_supplier()
    category = CategoryFactory()
    auto_category = CategoryFactory()

    manufacturer = Manufacturer.objects.create(name="test manufacturer")
    poprule = ManufacturerPopulatorRule.objects.create()
    poprule.manufacturers.add(manufacturer)

    populator = CategoryPopulator.objects.create(category=auto_category)
    populator.rules.add(poprule)

    product = create_product("test-sku", shop=shop, supplier=supplier, default_price=100)
    shop_product = product.get_shop_instance(shop)
    shop_product.product.manufacturer = manufacturer
    shop_product.product.save()
    shop_product.save()

    assert shop_product.categories.filter(pk=auto_category.pk).exists()

    product = shop_product.product
    product.manufacturer = None
    product.save()
    shop_product.save()

    # clear unmatching
    populator.clear_unmatching()

    assert not shop_product.categories.filter(pk=auto_category.pk).exists()

@pytest.mark.django_db
def test_category_populates_with_attribute(rf):
    activate("en")
    shop = get_default_shop()
    supplier = get_default_supplier()
    category = CategoryFactory()
    auto_category = CategoryFactory()

    past = datetime.now() - timedelta(days=2)
    future = datetime.now() + timedelta(days=2)

    attr1 = Attribute.objects.create(identifier="special_from", type=AttributeType.DATETIME, name="Special From")
    attr2 = Attribute.objects.create(identifier="special_to", type=AttributeType.DATETIME, name="Special To")

    rule1 = AttributePopulatorRule.objects.create(attribute=attr1, operator=ComparisonOperator.LTE, product_attr_name="created_on")
    rule2 = AttributePopulatorRule.objects.create(attribute=attr2, operator=ComparisonOperator.GTE, product_attr_name="created_on")

    populator = CategoryPopulator.objects.create(category=auto_category)
    populator.rules.add(rule1)
    populator.rules.add(rule2)

    product = create_product("test-sku", shop=shop, supplier=supplier, default_price=100)
    ProductAttribute.objects.create(product=product, attribute=attr1, datetime_value=past)  # special from two days ago
    ProductAttribute.objects.create(product=product, attribute=attr2, datetime_value=future)  # special to two days from now
    shop_product = product.get_shop_instance(shop)

    assert shop_product.categories.filter(pk=auto_category.pk).exists()

    product.created_on = past - timedelta(days=2)  # make product to past
    product.save()

    # clear unmatching
    populator.clear_unmatching()

    assert not shop_product.categories.filter(pk=auto_category.pk).exists()
