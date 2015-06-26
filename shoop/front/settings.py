# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

#: Spec string for the class used for creating Order from a Basket.
#:
#: This is the easiest way to customize the order creation process
#: without having to override a single URL or touch the ``shoop.front`` code.
SHOOP_BASKET_ORDER_CREATOR_SPEC = (
    "shoop.front.basket.order_creator:BasketOrderCreator")

#: Spec string for the Django CBV (or an API-compliant class) for the basket view.
#:
#: This view deals with ``/basket/``.
SHOOP_BASKET_VIEW_SPEC = (
    "shoop.front.views.basket:DefaultBasketView")

#: Spec string for the command dispatcher used when products are added/deleted/etc.
#: from the basket.
#:
#: This view deals with commands ``POST``ed to ``/basket/``.
SHOOP_BASKET_COMMAND_DISPATCHER_SPEC = (
    "shoop.front.basket.command_dispatcher:BasketCommandDispatcher")

#: Spec string for the update method dispatcher used when the basket is updated (usually
#: on the basket page).
SHOOP_BASKET_UPDATE_METHODS_SPEC = (
    "shoop.front.basket.update_methods:BasketUpdateMethods")

#: Spec string for the basket class used in the frontend.
#:
#: This is used to customize the behavior of the basket for a given installation,
#: for instance to modify prices of products based on certain conditions, etc.
SHOOP_BASKET_CLASS_SPEC = (
    "shoop.front.basket.objects:BaseBasket")

#: Spec string for the Django CBV (or an API-compliant class) for the checkout view.
#:
#: This is used to customize the behavior of the checkout process; most likely to
#: switch in a view with a different ``phase_specs``.
SHOOP_CHECKOUT_VIEW_SPEC = (
    "shoop.front.views.checkout:DefaultCheckoutView")
