# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import abc
import six
from django.http import HttpRequest
from django.utils.timezone import now


class PricingContextable(six.with_metaclass(abc.ABCMeta)):
    """
    Object that is or can be converted to a pricing context.

    Currently there exists two kind of `PricingContextable` objects:
    `PricingContext`(and its subclasses) and `HttpRequest`.

    .. note::

       Expression ``isinstance(request, PricingContextable)`` will
       return True for a ``request`` which is `HttpRequest`, because
       `HttpRequest` is registered as a subclass of this abstract base
       class.

    This abstract base class is just a helper to allow writing simpler
    type specifiers, since we want to allow passing `HttpRequest` as a
    pricing context even though it is not a `PricingContext`.
    """

    pass


PricingContextable.register(HttpRequest)


class PricingContext(PricingContextable):
    """
    Context for pricing.
    """

    def __init__(self, shop, customer, time=None, basket=None, supplier=None):
        """
        Initialize pricing context for shop and customer.

        :type shop: shuup.core.models.Shop
        :type customer: shuup.core.models.Contact
        :type time: datetime.datetime|None
        :type basket: shuup.core.models.Basket|None
        :type supplier: shuup.core.models.Supplier|None
        """
        assert shop is not None, "shop is required"
        assert customer is not None, "customer is required (may be AnonymousContact though)"

        self.shop = shop
        self.customer = customer
        self.basket = basket
        self.supplier = supplier
        if basket:
            assert basket.shop == shop, "shop must match with the basket"
        self.time = time if time is not None else now()
