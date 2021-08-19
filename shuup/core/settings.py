# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

"""
Settings of Shuup Core.

See :ref:`apps-settings` (in :obj:`shuup.apps`) for general information
about the Shuup settings system.  Especially, when inventing settings of
your own, the :ref:`apps-naming-settings` section is an important read.
"""

#: Which method is used to calculate the order identifiers ("order numbers").
#: May be either the string "id", a callable or a spec string, pointing
#: to a callable that must return a string given an ``order``.
SHUUP_ORDER_IDENTIFIER_METHOD = "id"


#: A list of order labels (2-tuples of internal identifier / visible name).
#:
#: Order labels serve as a simple taxonomy layer for easy "tagging" of orders even within
#: a single Shop. For instance, an installation could define ``"default"`` and ``"internal"``
#: order labels, which are can then be used in reports, admin filtering, etc.
SHUUP_ORDER_LABELS = [
    ("default", "Default"),
]

#: A list of "known keys" within the ``Order.payment_data`` property bag.
#:
#: The format of this setting is a list of 2-tuples of dict key / visible name,
#: for example ``[("ssn", "Social Security Number")]``.
#:
#: For installations where customizations may save some information, that is both
#: human-readable and potentially important, in ``payment_data``, this setting
#: may be used to make this data easily visible in the administration backend.
SHUUP_ORDER_KNOWN_PAYMENT_DATA_KEYS = []

#: A list of "known keys" within the ``Order.shipping_data`` property bag.
#:
#: The format of this setting is a list of 2-tuples of dict key / visible name,
#: for example ``[("shipping_instruction", "Special Shipping Instructions")]``.
#:
#: For installations where customizations may save some information, that is both
#: human-readable and potentially important, in ``shipping_data``, this setting
#: may be used to make this data easily visible in the administration backend.
SHUUP_ORDER_KNOWN_SHIPPING_DATA_KEYS = []

#: A list of "known keys" within the ``Order.extra_data`` property bag.
#:
#: The format of this setting is a list of 2-tuples of dict key / visible name,
#: for example ``[("wrapping_color", "Wrapping Paper Color")]``.
#:
#: For installations where customizations may save some information, that is both
#: human-readable and potentially important, in ``extra_data``, this setting
#: may be used to make this data easily visible in the administration backend.
SHUUP_ORDER_KNOWN_EXTRA_DATA_KEYS = []


#: The host URL for Shuup's telemetry (statistics) system.
SHUUP_TELEMETRY_HOST_URL = "https://telemetry.shuup.com"

#: The submission URL for Shuup's telemetry (statistics) system.
SHUUP_TELEMETRY_URL = "%s/collect/" % SHUUP_TELEMETRY_HOST_URL

#: The URL to fetch the Shuup installation `support id`.
SHUUP_SUPPORT_ID_URL = "%s/support-id" % SHUUP_TELEMETRY_HOST_URL

#: Default cache duration for various caches (in seconds).
SHUUP_DEFAULT_CACHE_DURATION = 60 * 30

#: Overrides for default cache durations by key namespace.
#: These settings override the possible defaults configured in
#: `shuup.core.cache.impl.DEFAULT_CACHE_DURATIONS`.
SHUUP_CACHE_DURATIONS = {}

#: Spec which defines the address formatter used to
#: format output string of an Address model instances.
SHUUP_ADDRESS_FORMATTER_SPEC = "shuup.core.utils.formatters:DefaultAddressFormatter"

#: Spec which defines an default address model form.
SHUUP_ADDRESS_MODEL_FORM = "shuup.core.utils.forms.MutableAddressForm"

#: A dictionary defining properties to override the default field properties of:
#: 1. the checkout address form
#: 2. the Address API
#:
#: Should map the field name (as a string) to a dictionary, containing the
#: overriding Django form field properties, as in the following
#: example (makes the postal code a required field):
#:
#: SHUUP_ADDRESS_FIELD_PROPERTIES = {
#:    "postal_code": {"required": True}
#: }
#:
#: Some of the Django form field properties will not affect Address API.
#: The valid set of properties are those defined by the Serializer fields core arguments
#: like `read_only`, `required`, `allow_null`, etc. See the Django Rest Framework documentation
#: for more properties.
#:
#: It should be noted, however, that overriding some of the settings (such as making a
#: required field non-required) could create other validation issues.
SHUUP_ADDRESS_FIELD_PROPERTIES = {}

#: Indicates maximum days for daily data included to one telemetry request
SHUUP_MAX_DAYS_IN_TELEMETRY = 180

#: Spec which defines if shop product categories
#: will be automatically populated on save and
#: when the shop_product categories change.
#:
#: Example A:
#: shop_product.categories = []
#: shop_product.primary_category = "A"
#: shop_product.save()
#: => "A" will be added to categories
#:
#: Example B:
#: shop_product.primary_category = None
#: shop_product.categories = ["A", "B"]
#: => "A" will be made the shop_product.primary_category
SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES = True

#: Spec which defines a list of handlers of page errors,
#: overwriting Django's default error handlers configured in urls.py (if some).
#:
#: Shuup will iterate over all handlers in order to determinate
#: if some of them can handle the error. In case of no handlers able to
#: do the job, a blank response will be returned.
#:
#: A handler must be a subclass of `shuup.core.error_handling.ErrorPageHandler`.
#:
#: If no handler is set (blank), Shuup will use the default Django's handlers.
SHUUP_ERROR_PAGE_HANDLERS_SPEC = []

#: Spec which defines shop product supplier strategy.
#: Used to determine how the supplier is selected for source line and orderability checks.
#:
#: This spec defines class, which should implement `get_supplier` method. For this method
#: the current shop product with customer, quantity and shipping address is passed as kwargs.
SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY = "shuup.core.suppliers.FirstSupplierStrategy"

#: Spec which provides the current shop for a given request and a set of parameters.
SHUUP_REQUEST_SHOP_PROVIDER_SPEC = "shuup.core.shop_provider.DefaultShopProvider"


#: Spec that defines the task runner.
#: The task runner is an object that can handle dynamic task execution
#: by receiving a function spec and a set of arguments.
#:
#: Custom task runners can be implemented to enable asynchronous
#: execution through tools like Celery.
#:
#: The default implementation is a basic task runner that will
#: load the function and call it passing the arguments received.
#:
SHUUP_TASK_RUNNER = "shuup.core.tasks.DefaultTaskRunner"
