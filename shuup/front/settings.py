# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

#: Spec string for the class used for creating Order from a Basket.
#:
#: This is the easiest way to customize the order creation process
#: without having to override a single URL or touch the ``shuup.front`` code.
SHUUP_BASKET_ORDER_CREATOR_SPEC = (
    "shuup.core.basket.order_creator:BasketOrderCreator")

#: Spec string for the Django CBV (or an API-compliant class) for the basket view.
#:
#: This view deals with ``/basket/``.
SHUUP_BASKET_VIEW_SPEC = (
    "shuup.front.views.basket:DefaultBasketView")

#: Spec string for the command dispatcher used when products are added/deleted/etc.
#: from the basket.
#:
#: This view deals with commands ``POST``ed to ``/basket/``.
SHUUP_BASKET_COMMAND_DISPATCHER_SPEC = (
    "shuup.core.basket.command_dispatcher:BasketCommandDispatcher")

#: Spec string for the update method dispatcher used when the basket is updated (usually
#: on the basket page).
SHUUP_BASKET_UPDATE_METHODS_SPEC = (
    "shuup.front.basket.update_methods:BasketUpdateMethods")

#: Spec string for the basket class used in the frontend.
#:
#: This is used to customize the behavior of the basket for a given installation,
#: for instance to modify prices of products based on certain conditions, etc.
SHUUP_BASKET_CLASS_SPEC = (
    "shuup.front.basket.objects:BaseBasket")

#: The spec string defining which basket storage class to use for the frontend.
#:
#: Basket storages are responsible for persisting visitor basket state,
#: the default stores the basket to database (DatabaseBasketStorage)
#: Custom storage backends could use caches, flat files, etc. if required.
SHUUP_BASKET_STORAGE_CLASS_SPEC = (
    "shuup.front.basket.storage:DatabaseBasketStorage")

#: Spec string for the Django CBV (or an API-compliant class) for the checkout view.
#:
#: This is used to customize the behavior of the checkout process; most likely to
#: switch in a view with a different ``phase_specs``.
SHUUP_CHECKOUT_VIEW_SPEC = (
    "shuup.front.views.checkout:DefaultCheckoutView")

#: Default product lists facet configuration
#:
#: This configuration will be used if the configuration is not set from admin
SHUUP_FRONT_DEFAULT_SORT_CONFIGURATION = {
    "sort_products_by_name": True,
    "sort_products_by_name_ordering": 1,
    "sort_products_by_price": True,
    "sort_products_by_price_ordering": 2
}

#: Default cache duration for template helpers
#:
#: Cache duration in seconds for front template helpers. Default 30 minutes.
SHUUP_TEMPLATE_HELPERS_CACHE_DURATION = 60*30

#: A dictionary defining properties to override the default field properties of the
#: person contact form. Should map the field name (as a string) to a dictionary
#: containing the overriding Django form field properties, as in the following
#: example which makes the gender field hidden:
#:
#: SHUUP_PERSON_CONTACT_FIELD_PROPERTIES = {
#:    "gender": {"widget": forms.HiddenInput()}
#: }
#:
#: It should be noted, however, that overriding some settings (such as making a
#: required field non-required) could create other validation issues.
SHUUP_PERSON_CONTACT_FIELD_PROPERTIES = {}

#: A dictionary defining properties to override the default field properties of the
#: confirm form. Should map the field name (as a string) to a dictionary
#: containing the overriding Django form field properties, as in the following
#: example which makes the gender field hidden:
#:
#: SHUUP_CHECKOUT_CONFIRM_FORM_PROPERTIES = {
#:    "marketing": {"initial": True},
#:    "comment": {"widget": forms.HiddenInput()}
#: }
#:
#: It should be noted, however, that overriding some settings (such as making a
#: required field non-required) could create other validation issues.
SHUUP_CHECKOUT_CONFIRM_FORM_PROPERTIES = {}
#: Method for override front models urls for product and category. 
#: For example: default product url: www.domain.com/p/pk-slug
#: can be changed to: www.domain.com/product/slug.
#: arguments: context,
#:            model,
#:            absolute (bool)
#: return: url
#: Const SHUUP_MODEL_URL_RESOLVER_SPEC takes string as path to your method: 
#: app.urls.method_name
SHUUP_MODEL_URL_RESOLVER_SPEC = 'shuup.front.utils.urls.model_url'
