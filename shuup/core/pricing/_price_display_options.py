# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


class PriceDisplayOptions(object):
    """
    Price display options.

    Parameters on how prices should be rendered.
    """
    def __init__(self, include_taxes=None, show_prices=True):
        """
        Initialize price display options.

        :type include_taxes: bool|None
        :param include_taxes:
          Whether include taxes to rendered prices or not.  If None,
          show prices in their original taxness.
        :type show_prices: bool
        :param show_prices:
          Whether show prices at all.
        """
        self.include_taxes = include_taxes
        self.show_prices = show_prices

    @property
    def hide_prices(self):
        return not self.show_prices

    @classmethod
    def from_context(cls, context):
        """
        Get price display options from context.

        :type context: jinja2.runtime.Context|dict
        :rtype: PriceDisplayOptions
        """
        options = context.get('price_display_options')

        if options is None:
            request = context.get('request')  # type: django.http.HttpRequest
            options = getattr(request, 'price_display_options', None)

        if options is None:
            options = cls()

        return options

    def set_for_request(self, request):
        """
        Set price display options of given request to self.
        """
        request.price_display_options = self
