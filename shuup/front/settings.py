# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


#: This is used to get the login form for the login dropdown in navigation.jinja file.
SHUUP_LOGIN_VIEW = (
    "shuup.front.apps.auth.views:LoginView")

#: Spec string for the class used to create Order from a Basket.
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

#: Spec string for the command dispatcher. Used when products are added/deleted/etc
#: from the basket.
#:
#: This view deals with commands ``POST``ed to ``/basket/``.
SHUUP_BASKET_COMMAND_DISPATCHER_SPEC = (
    "shuup.core.basket.command_dispatcher:BasketCommandDispatcher")

#: Spec string for the update method dispatcher. Used when the basket is updated (usually
#: on the basket page).
SHUUP_BASKET_UPDATE_METHODS_SPEC = (
    "shuup.front.basket.update_methods:BasketUpdateMethods")

#: Spec string for the basket class, used in the frontend.
#:
#: This is used to customize the behavior of the basket for a given installation,
#: for instance to modify prices of products based on certain condition.
SHUUP_BASKET_CLASS_SPEC = (
    "shuup.front.basket.objects:BaseBasket")

#: The spec string, defining which basket storage class to use for the frontend.
#:
#: Basket storages are responsible for persisting visitor basket state.
#: The default stores the basket to database (`DatabaseBasketStorage`).
#: Custom storage backends could use caches, flat files, etc. if required.
SHUUP_BASKET_STORAGE_CLASS_SPEC = (
    "shuup.front.basket.storage:DatabaseBasketStorage")

#: Spec string for the Django CBV (or an API-compliant class) for the checkout view.
#:
#: This is used to customize the behavior of the checkout process; most likely to
#: switch in a view with a different ``phase_specs``.
SHUUP_CHECKOUT_VIEW_SPEC = (
    "shuup.front.views.checkout:DefaultCheckoutView")

#: Default product lists facet configuration.
#:
#: This configuration will be used if the configuration is not set from admin.
SHUUP_FRONT_DEFAULT_SORT_CONFIGURATION = {
    "sort_products_by_name": True,
    "sort_products_by_name_ordering": 1,
    "sort_products_by_price": True,
    "sort_products_by_price_ordering": 2
}

#: Default product context for product detail view
#:
#: Override this configuration for quick per project optimization or for adding
#: something extra for your custom, templates, snippets and plugins.
SHUUP_FRONT_PRODUCT_CONTEXT_SPEC = (
    "shuup.front.utils.product:get_default_product_context")

#: Default cache duration for template helpers (in seconds).
#:
#: Cache duration in seconds for front template helpers. Default: 30 minutes.
SHUUP_TEMPLATE_HELPERS_CACHE_DURATION = 60*30

#: A dictionary, defining properties to override the default field properties of the
#: person contact form. Should map the field name (as a string) to a dictionary.
#: The dictionary should contain the overriding Django form field properties, as in
#: the following example (makes the `gender` field hidden):
#:
#: SHUUP_PERSON_CONTACT_FIELD_PROPERTIES = {
#:    "gender": {"widget": forms.HiddenInput()}
#: }
#:
#: It should be noted, however, that overriding some of the settings (such as making a
#: required field non-required) could create other validation issues.
SHUUP_PERSON_CONTACT_FIELD_PROPERTIES = {}

#: A dictionary defining properties to override the default field properties of the
#: `confirm` form. Should map the field name (as a string) to a dictionary.
#: The dictionary should contain the overriding Django form field properties, as in
#: the following example (makes the `gender` field hidden):
#:
#: SHUUP_CHECKOUT_CONFIRM_FORM_PROPERTIES = {
#:    "marketing": {"initial": True},
#:    "comment": {"widget": forms.HiddenInput()}
#: }
#:
#: It should be noted, however, that overriding some of the settings (such as making a
#: required field non-required) could create other validation issues.
SHUUP_CHECKOUT_CONFIRM_FORM_PROPERTIES = {}

#: The default "Shuup powered by" content. This content is rendered in theme bottom
#: by default at `shuup.front.templates.shuup.front.macros.footer.jinja`.
SHUUP_FRONT_POWERED_BY_CONTENT = """
    <p class="powered">Powered by <a target="_blank" href="https://shuup.com">Shuup</a></p>
""".strip()

#: Override sort and filters labels with your own.
#:
#: Define dictionary with field identifier as key and new label as value.
#:
#: SHUUP_FRONT_OVERRIDE_SORTS_AND_FILTERS_LABELS_LOGIC = {
#:      "manufacturers": _("Brands"),
#:      "suppliers": _("Filter by vendor")
#: }
#:
SHUUP_FRONT_OVERRIDE_SORTS_AND_FILTERS_LABELS_LOGIC = {}


#: Maximum allowed file size (in bytes) for uploads, when posting to
#: `shuup.front.views.upload.media_upload`.
#:
SHUUP_FRONT_MAX_UPLOAD_SIZE = 500000
