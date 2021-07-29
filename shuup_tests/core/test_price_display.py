# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Tests for utils.price_display and the price filters.
"""

import django.template
import django_jinja.backend
import pytest
from decimal import Decimal
from django.conf import settings
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import patch

from shuup.apps.provides import override_provides
from shuup.core.models import (
    AnonymousContact,
    Order,
    OrderLine,
    OrderLineType,
    Product,
    ProductCatalogPrice,
    Shop,
    ShopProduct,
)
from shuup.core.order_creator import OrderSource
from shuup.core.pricing import (
    PriceDisplayOptions,
    PriceInfo,
    PricingModule,
    TaxfulPrice,
    TaxlessPrice,
    get_pricing_module,
)
from shuup.front.basket.objects import BaseBasket
from shuup.testing.factories import (
    create_default_tax_rule,
    create_product,
    create_random_person,
    get_default_shop,
    get_default_supplier,
    get_default_tax,
    get_default_tax_class,
)

PRICING_MODULE_SPEC = __name__ + ":DummyPricingModule"

original_pricing_module = settings.SHUUP_PRICING_MODULE
original_discount_modules = settings.SHUUP_DISCOUNT_MODULES
pricing_overrider = override_provides("pricing_module", [PRICING_MODULE_SPEC])


def setup_module(module):
    settings.SHUUP_PRICING_MODULE = "dummy_pricing_module"
    settings.SHUUP_DISCOUNT_MODULES = []
    pricing_overrider.__enter__()


def teardown_module(module):
    pricing_overrider.__exit__(None, None, None)
    settings.SHUUP_PRICING_MODULE = original_pricing_module
    settings.SHUUP_DISCOUNT_MODULES = original_discount_modules


class DummyPricingModule(PricingModule):
    identifier = "dummy_pricing_module"

    def get_price_info(self, context, product, quantity=1):
        return _get_price_info(context.shop, product, quantity)

    def index_shop_product(self, shop_product, **kwargs):
        is_variation_parent = shop_product.product.is_variation_parent()

        # index the price of all children shop products
        if is_variation_parent:
            children_shop_product = ShopProduct.objects.select_related("product", "shop").filter(
                shop=shop_product.shop, product__variation_parent_id=shop_product.product_id
            )
            for child_shop_product in children_shop_product:
                self.index_shop_product(child_shop_product)
        else:
            for supplier_id in shop_product.suppliers.values_list("pk", flat=True):
                ProductCatalogPrice.objects.update_or_create(
                    product_id=shop_product.product_id,
                    shop_id=shop_product.shop_id,
                    supplier_id=supplier_id,
                    catalog_rule=None,
                    defaults=dict(price_value=shop_product.default_price_value or Decimal()),
                )


def _get_price_info(shop, product=None, quantity=2):
    if not product:
        product = Product(sku="6.0745")
    # SKU of product defines the price :)
    price = shop.create_price(product.sku)
    return PriceInfo(quantity * price, quantity * 4 * price, quantity)


def test_pricing_module_is_active():
    """
    Make sure that our custom pricing module is active.
    """
    shop = Shop(currency="USD", prices_include_tax=False)
    customer = AnonymousContact()
    product = Product(sku="6.0745")

    pricing_mod = get_pricing_module()
    pricing_ctx = pricing_mod.get_context_from_data(shop, customer)

    pi = product.get_price_info(pricing_ctx, quantity=2)

    price = shop.create_price
    assert pi.price == price("12.149")
    assert pi.base_price == price("48.596")
    assert pi.quantity == 2
    assert pi.discounted_unit_price == price("6.0745")
    assert pi.base_unit_price == price("24.298")
    assert pi.discount_rate == Decimal("0.75")


def test_render_price_property():
    pass


TEST_DATA = [
    # (jinja expression, expected result)
    ("prod|price", "$6.07"),
    ("prod|base_price", "$24.30"),
    ("prod|discount_amount", "$18.22"),
    ("prod|discounted_unit_price", "$6.07"),
    ("prod|base_unit_price", "$24.30"),
    ("prod|unit_discount_amount", "$18.22"),
    ("prod|is_discounted", "True"),
    ("prod|discount_percent", "75%"),
    ("prod|discount_rate", "0.75"),
    ("var_prod|price_range|safe", "('$4.50', '$12.00')"),
    ("prod|price(quantity=2)", "$12.15"),
    ("prod|price(quantity=2, include_taxes=False)", "$12.15"),
    ("prod|price(quantity=2, include_taxes=True)", "$18.22"),
    ("prod|base_price(quantity=2)", "$48.60"),
    ("prod|base_unit_price(quantity=2)", "$24.30"),
    ("prod|discount_amount(quantity=2)", "$36.45"),
    ("prod|discounted_unit_price(quantity=2)", "$6.07"),
    ("prod|unit_discount_amount(quantity=2)", "$18.22"),
    ("prod|is_discounted(quantity=2)", "True"),
    ("prod|discount_percent(quantity=2)", "75%"),
    ("prod|discount_rate(quantity=2)", "0.75"),
    ("sline|price", "$12.15"),
    ("sline|base_price", "$48.60"),
    ("sline|base_unit_price", "$24.30"),
    ("sline|discount_amount", "$36.45"),
    ("sline|discounted_unit_price", "$6.07"),
    ("sline|unit_discount_amount", "$18.22"),
    ("sline|is_discounted", "True"),
    ("sline|discount_percent", "75%"),
    ("sline|discount_rate", "0.75"),
    ("bline|price", "$12.15"),
    ("bline|base_price", "$48.60"),
    ("bline|base_unit_price", "$24.30"),
    ("bline|discount_amount", "$36.45"),
    ("bline|discounted_unit_price", "$6.07"),
    ("bline|unit_discount_amount", "$18.22"),
    ("bline|is_discounted", "True"),
    ("bline|discount_percent", "75%"),
    ("bline|discount_rate", "0.75"),
    ("oline|price", "$12.15"),
    ("oline|base_price", "$48.60"),
    ("oline|base_unit_price", "$24.30"),
    ("oline|discount_amount", "$36.45"),
    ("oline|discounted_unit_price", "$6.07"),
    ("oline|unit_discount_amount", "$18.22"),
    ("oline|is_discounted", "True"),
    ("oline|discount_percent", "75%"),
    ("oline|discount_rate", "0.75"),
    ("order|total_price", "$50.00"),
    ("order|total_price(include_taxes=False)", "$50.00"),
    ("order|total_price(include_taxes=True)", "$100.00"),
]


@pytest.mark.parametrize("expr,expected_result", TEST_DATA)
@pytest.mark.django_db
def test_filter(expr, expected_result, reindex_catalog):
    (engine, context) = _get_template_engine_and_context(create_var_product=True)
    reindex_catalog()
    template = engine.from_string("{{ " + expr + "  }}")
    try:
        result = template.render(context)
    except AttributeError as error:
        assert type(error) == expected_result
    else:
        assert result == expected_result


@pytest.mark.parametrize("expr,expected_result", TEST_DATA)
@pytest.mark.django_db
def test_filter_cache(expr, expected_result, reindex_catalog):
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_filter_cache",
            }
        }
    ):
        (engine, context) = _get_template_engine_and_context(create_var_product=True)
        reindex_catalog()
        template = engine.from_string("{{ " + expr + "  }}")
        # run 2 times, the first call should cache and the second read from the cache
        for cache_test in range(2):
            try:
                result = template.render(context)
            except AttributeError as error:
                assert type(error) == expected_result
            else:
                assert result == expected_result


@pytest.mark.django_db
def test_filter_parameter():
    (engine, context) = _get_template_engine_and_context()
    result = engine.from_string("{{ prod|price(quantity=2, include_taxes=True) }}")
    assert result.render(context) == "$18.22"

    result = engine.from_string("{{ prod|price(quantity=2) }}")
    assert result.render(context) == "$12.15"


@pytest.mark.django_db
def test_filter_parameter_contact_groups():
    customer_price = 10.3
    anonymous_price = 14.6

    def get_price_info_mock(context, product, quantity=1):
        if context.customer.get_default_group() == AnonymousContact().get_default_group():
            price = context.shop.create_price(anonymous_price)
        else:
            price = context.shop.create_price(customer_price)
        return PriceInfo(quantity * price, quantity * price, quantity)

    with patch.object(DummyPricingModule, "get_price_info", side_effect=get_price_info_mock):
        (engine, context) = _get_template_engine_and_context(product_sku="123")
        # test with anonymous
        context["request"].customer = AnonymousContact()
        context["request"].person = context["request"].customer
        result = engine.from_string("{{ prod|price(quantity=2) }}")
        assert result.render(context) == "$%0.2f" % (anonymous_price * 2)

        # Get fresh content. I guess the prices shouldn't change between request.
        (engine, context) = _get_template_engine_and_context(product_sku="1234")
        # test with customer
        context["request"].customer = create_random_person()
        context["request"].person = context["request"].customer
        result = engine.from_string("{{ prod|price(quantity=2) }}")
        assert result.render(context) == "$%0.2f" % (customer_price * 2)


def _get_template_engine_and_context(product_sku="6.0745", create_var_product=False):
    engine = django.template.engines["jinja2"]
    assert isinstance(engine, django_jinja.backend.Jinja2)

    shop = get_default_shop()
    shop.currency = "USD"
    shop.prices_include_tax = False
    shop.save()

    request = RequestFactory().get("/")
    request.shop = shop
    request.customer = AnonymousContact()
    request.person = request.customer
    PriceDisplayOptions(include_taxes=False).set_for_request(request)
    tax = get_default_tax()
    create_default_tax_rule(tax)
    tax_class = get_default_tax_class()
    order, order_line = _get_order_and_order_line(request)

    product = create_product(sku=product_sku, shop=shop, tax_class=tax_class)
    supplier = get_default_supplier(shop)

    if create_var_product:
        var_product = create_product(sku="32.9", shop=shop, tax_class=tax_class)
        child_product_1 = create_product(
            sku="4.50", shop=shop, tax_class=tax_class, supplier=supplier, default_price="4.5"
        )
        child_product_2 = create_product(
            sku="12.00", shop=shop, tax_class=tax_class, supplier=supplier, default_price="12"
        )
        child_product_1.link_to_parent(var_product, variables={"color": "red"})
        child_product_2.link_to_parent(var_product, variables={"color": "blue"})

    context = {
        "request": request,
        "prod": product,
        "var_prod": var_product if create_var_product else None,
        # TODO: Test also with variant products
        "sline": _get_source_line(request),
        "bline": _get_basket_line(request),
        "oline": order_line,
        "order": order,
    }

    return (engine, context)


def _get_source_line(request):
    source = OrderSource(request.shop)
    return _create_line(source, Product(sku="6.0745"))


def _get_basket_line(request):
    basket = BaseBasket(request)
    return _create_line(basket, Product(sku="6.0745"))


def _create_line(source, product):
    pi = _get_price_info(source.shop)
    return source.create_line(
        type=OrderLineType.PRODUCT,
        product=product,
        base_unit_price=pi.base_unit_price,
        quantity=pi.quantity,
        discount_amount=pi.discount_amount,
    )


def _get_order_and_order_line(request):
    order = Order(
        shop=request.shop,
        currency=request.shop.currency,
        prices_include_tax=request.shop.prices_include_tax,
    )
    order.taxful_total_price = TaxfulPrice("100", request.shop.currency)
    order.taxless_total_price = TaxlessPrice("50", request.shop.currency)
    pi = _get_price_info(request.shop, Product(sku="6.0745"), quantity=2)
    return (
        order,
        OrderLine(
            order=order,
            base_unit_price=pi.base_unit_price,
            discount_amount=pi.discount_amount,
            quantity=pi.quantity,
        ),
    )
