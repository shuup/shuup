"""
Tests for utils.price_display and the price filters.
"""

from decimal import Decimal

import django.template
import django_jinja.backend
import pytest
from django.conf import settings
from django.test.client import RequestFactory

from shuup.apps.provides import override_provides
from shuup.core.models import (
    AnonymousContact, Order, OrderLine, OrderLineType, Product, Shop
)
from shuup.core.order_creator import OrderSource
from shuup.core.pricing import (
    get_pricing_module, PriceInfo, PricingModule, TaxlessPrice
)
from shuup.front.basket.objects import BaseBasket
from shuup.testing.factories import (
    create_default_tax_rule, get_default_tax, get_default_tax_class
)

PRICING_MODULE_SPEC = __name__ + ':DummyPricingModule'

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


def _get_price_info(shop, product=None, quantity=2):
    if not product:
        product = Product(sku='6.0745')
    # SKU of product defines the price :)
    price = shop.create_price(product.sku)
    return PriceInfo(quantity * price, quantity * 4 * price, quantity)


def test_pricing_module_is_active():
    """
    Make sure that our custom pricing module is active.
    """
    shop = Shop(currency='USD', prices_include_tax=False)
    customer = AnonymousContact()
    product = Product(sku='6.0745')

    pricing_mod = get_pricing_module()
    pricing_ctx = pricing_mod.get_context_from_data(shop, customer)

    pi = product.get_price_info(pricing_ctx, quantity=2)

    price = shop.create_price
    assert pi.price == price('12.149')
    assert pi.base_price == price('48.596')
    assert pi.quantity == 2
    assert pi.discounted_unit_price == price('6.0745')
    assert pi.base_unit_price == price('24.298')
    assert pi.discount_rate == Decimal('0.75')


def test_render_price_property():
    pass


TEST_DATA = [
    # (jinja expression, expected result)
    ('prod|price', '$6.07'),
    ('prod|base_price', '$24.30'),
    ('prod|discount_amount', '$18.22'),
    ('prod|discounted_unit_price', '$6.07'),
    ('prod|base_unit_price', '$24.30'),
    ('prod|unit_discount_amount', '$18.22'),
    ('prod|is_discounted', 'True'),
    ('prod|discount_percent', '75%'),
    ('prod|discount_rate', '0.75'),

    ('prod|price(quantity=2)', '$12.15'),
    ('prod|price(quantity=2, include_taxes=False)', '$12.15'),
    ('prod|price(quantity=2, include_taxes=True)', '$18.22'),
    ('prod|base_price(quantity=2)', '$48.60'),
    ('prod|base_unit_price(quantity=2)', '$24.30'),
    ('prod|discount_amount(quantity=2)', '$36.45'),
    ('prod|discounted_unit_price(quantity=2)', '$6.07'),
    ('prod|unit_discount_amount(quantity=2)', '$18.22'),
    ('prod|is_discounted(quantity=2)', 'True'),
    ('prod|discount_percent(quantity=2)', '75%'),
    ('prod|discount_rate(quantity=2)', '0.75'),

    ('sline|price', '$12.15'),
    ('sline|base_price', '$48.60'),
    ('sline|base_unit_price', '$24.30'),
    ('sline|discount_amount', '$36.45'),
    ('sline|discounted_unit_price', '$6.07'),
    ('sline|unit_discount_amount', '$18.22'),
    ('sline|is_discounted', 'True'),
    ('sline|discount_percent', '75%'),
    ('sline|discount_rate', '0.75'),

    ('bline|price', '$12.15'),
    ('bline|base_price', '$48.60'),
    ('bline|base_unit_price', '$24.30'),
    ('bline|discount_amount', '$36.45'),
    ('bline|discounted_unit_price', '$6.07'),
    ('bline|unit_discount_amount', '$18.22'),
    ('bline|is_discounted', 'True'),
    ('bline|discount_percent', '75%'),
    ('bline|discount_rate', '0.75'),

    ('oline|price', '$12.15'),
    ('oline|base_price', '$48.60'),
    ('oline|base_unit_price', '$24.30'),
    ('oline|discount_amount', '$36.45'),
    ('oline|discounted_unit_price', '$6.07'),
    ('oline|unit_discount_amount', '$18.22'),
    ('oline|is_discounted', 'True'),
    ('oline|discount_percent', '75%'),
    ('oline|discount_rate', '0.75'),
]


@pytest.mark.parametrize("expr,expected_result", TEST_DATA)
@pytest.mark.django_db
def test_filter(expr, expected_result):
    (engine, context) = _get_template_engine_and_context()
    template = engine.from_string('{{ ' + expr + '  }}')
    try:
        result = template.render(context)
    except AttributeError as error:
        assert type(error) == expected_result
    else:
        assert result == expected_result


def _get_template_engine_and_context():
    engine = django.template.engines['jinja2']
    assert isinstance(engine, django_jinja.backend.Jinja2)

    request = RequestFactory().get('/')
    request.shop = Shop(currency='USD', prices_include_tax=False)
    request.customer = AnonymousContact()
    request.person = request.customer
    tax = get_default_tax()
    create_default_tax_rule(tax)
    tax_class = get_default_tax_class()

    context = {
        'request': request,
        'prod': Product(sku='6.0745', tax_class=tax_class),
        # TODO: Test also with variant products
        'sline': _get_source_line(request),
        'bline': _get_basket_line(request),
        'oline': _get_order_line(request),
    }

    return (engine, context)

def _get_source_line(request):
    source = OrderSource(request.shop)
    return _create_line(source, Product(sku='6.0745'))


def _get_basket_line(request):
    basket = BaseBasket(request)
    return _create_line(basket, Product(sku='6.0745'))


def _create_line(source, product):
    pi = _get_price_info(source.shop)
    return source.create_line(
        type=OrderLineType.PRODUCT,
        product=product,
        base_unit_price=pi.base_unit_price,
        quantity=pi.quantity,
        discount_amount=pi.discount_amount,
    )


def _get_order_line(request):
    order = Order(
        shop=request.shop,
        currency=request.shop.currency,
        prices_include_tax=request.shop.prices_include_tax,
    )
    pi = _get_price_info(request.shop, Product(sku='6.0745'), quantity=2)
    return OrderLine(
        order=order,
        base_unit_price=pi.base_unit_price,
        discount_amount=pi.discount_amount,
        quantity=pi.quantity,
    )
