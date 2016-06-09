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
