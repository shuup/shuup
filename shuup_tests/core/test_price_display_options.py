import pytest

from shuup.core.pricing import PriceDisplayOptions


def test_price_display_options_default():
    options = PriceDisplayOptions()
    assert options.show_prices is True
    assert options.hide_prices is False
    assert options.include_taxes is None


def test_price_display_options_more():
    options = PriceDisplayOptions(show_prices=False)
    assert options.show_prices is False
    assert options.hide_prices is True
    assert options.include_taxes is None

    options = PriceDisplayOptions(include_taxes=True)
    assert options.show_prices is True
    assert options.include_taxes is True

    options = PriceDisplayOptions(include_taxes=False)
    assert options.show_prices is True
    assert options.include_taxes is False

def test_price_display_set_option():
    options = PriceDisplayOptions(show_prices=False)
    assert options.show_prices is False
    assert options.include_taxes is None
    options.set_option("show_prices", True)
    assert options.show_prices is True
    options.set_option("include_taxes", True)
    assert options.include_taxes is True

    with pytest.raises(ValueError):
        options.set_option("not_an_option", True)
