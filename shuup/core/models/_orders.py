# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import datetime
from collections import defaultdict
from decimal import Decimal
from itertools import chain

import six
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q
from django.db.transaction import atomic
from django.utils.crypto import get_random_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from shuup.core import taxing
from shuup.core.excs import (
    InvalidRefundAmountException, NoPaymentToCreateException,
    NoProductsToShipException, NoRefundToCreateException,
    NoShippingAddressException, RefundArbitraryRefundsNotAllowedException,
    RefundExceedsAmountException, RefundExceedsQuantityException
)
from shuup.core.fields import (
    CurrencyField, InternalIdentifierField, LanguageField, MoneyValueField,
    UnsavedForeignKey
)
from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.core.settings_provider import ShuupSettings
from shuup.core.signals import (
    order_changed, order_status_changed, payment_created, refund_created,
    shipment_created, shipment_created_and_processed
)
from shuup.utils.analog import define_log_model, LogEntryKind
from shuup.utils.dates import local_now, to_aware
from shuup.utils.django_compat import force_text
from shuup.utils.money import Money
from shuup.utils.properties import (
    MoneyPropped, TaxfulPriceProperty, TaxlessPriceProperty
)

from ._order_lines import OrderLine, OrderLineType
from ._order_utils import get_order_identifier, get_reference_number
from ._products import Product
from ._suppliers import Supplier


class PaymentStatus(Enum):
    NOT_PAID = 0
    PARTIALLY_PAID = 1
    FULLY_PAID = 2
    CANCELED = 3
    DEFERRED = 4

    class Labels:
        NOT_PAID = _('not paid')
        PARTIALLY_PAID = _('partially paid')
        FULLY_PAID = _('fully paid')
        CANCELED = _('canceled')
        DEFERRED = _('deferred')


class ShippingStatus(Enum):
    NOT_SHIPPED = 0
    PARTIALLY_SHIPPED = 1
    FULLY_SHIPPED = 2

    class Labels:
        NOT_SHIPPED = _('not shipped')
        PARTIALLY_SHIPPED = _('partially shipped')
        FULLY_SHIPPED = _('fully shipped')


class OrderStatusRole(Enum):
    NONE = 0
    INITIAL = 1
    COMPLETE = 2
    CANCELED = 3
    PROCESSING = 4
    # TODO: Failed state?

    class Labels:
        NONE = _('none')
        INITIAL = _('Initial')
        COMPLETE = _('Complete')
        CANCELED = _('Canceled')
        PROCESSING = _('Processing')


class DefaultOrderStatus(Enum):
    NONE = "none"
    INITIAL = "initial"
    COMPLETE = "complete"
    CANCELED = "canceled"
    PROCESSING = "processing"
    # TODO: Failed state?

    class Labels:
        NONE = _('none')
        INITIAL = _('Received')
        COMPLETE = _('Complete')
        CANCELED = _('Canceled')
        PROCESSING = _('In Progress')


class OrderStatusQuerySet(TranslatableQuerySet):
    def _default_for_role(self, role):
        """
        Get the default order status for the given role.

        :param role: The role to look for.
        :type role: OrderStatusRole
        :return: The OrderStatus.
        :rtype: OrderStatus
        """
        try:
            return self.get(default=True, role=role)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist("Error! No default `%s` OrderStatus exists." % getattr(role, "label", role))

    def get_default_initial(self):
        return self._default_for_role(OrderStatusRole.INITIAL)

    def get_default_processing(self):
        return self._default_for_role(OrderStatusRole.PROCESSING)

    def get_default_canceled(self):
        return self._default_for_role(OrderStatusRole.CANCELED)

    def get_default_complete(self):
        return self._default_for_role(OrderStatusRole.COMPLETE)


@python_2_unicode_compatible
class OrderStatus(TranslatableModel):
    identifier = InternalIdentifierField(
        db_index=True, blank=False, editable=True, unique=True,
        help_text=_("Internal identifier for status. This is used to identify and distinguish the statuses in Shuup.")
    )
    ordering = models.IntegerField(db_index=True, default=0, verbose_name=_('ordering'),
                                   help_text=_("The processing order of statuses. Default is always processed first."))
    role = EnumIntegerField(
        OrderStatusRole, db_index=True,
        default=OrderStatusRole.NONE, verbose_name=_('role'),
        help_text=_("The role of this status. One role can have multiple order statuses."))
    default = models.BooleanField(
        default=False, db_index=True, verbose_name=_('default'),
        help_text=_("Defines if the status should be considered as default. Default is always processed first."))

    is_active = models.BooleanField(
        default=True, db_index=True, verbose_name=_('is active'), help_text=_("Defines if the status is usable."))

    objects = OrderStatusQuerySet.as_manager()

    translations = TranslatedFields(
        name=models.CharField(verbose_name=_("name"), max_length=64, help_text=_("Name of the order status.")),
        public_name=models.CharField(
            verbose_name=_('public name'), max_length=64, help_text=_("The name shown to the customers in shop front."))
    )

    class Meta:
        unique_together = ("identifier", "role")
        verbose_name = _('order status')
        verbose_name_plural = _('order statuses')

    def __str__(self):
        return force_text(self.safe_translation_getter("name", default=self.identifier))

    def save(self, *args, **kwargs):
        super(OrderStatus, self).save(*args, **kwargs)
        if self.default and self.role != OrderStatusRole.NONE:
            # If this status is the default, make the others for this role non-default.
            OrderStatus.objects.filter(role=self.role).exclude(pk=self.pk).update(default=False)


class OrderStatusManager(object):
    def __init__(self):
        self.default_statuses = [
            {
                "name": DefaultOrderStatus.INITIAL.label,
                "public_name": DefaultOrderStatus.INITIAL.label,
                "role": OrderStatusRole.INITIAL,
                "identifier": DefaultOrderStatus.INITIAL.value,
                "default": True,
                "is_active": True
            },
            {
                "name": DefaultOrderStatus.PROCESSING.label,
                "public_name": DefaultOrderStatus.PROCESSING.label,
                "role": OrderStatusRole.PROCESSING,
                "identifier": DefaultOrderStatus.PROCESSING.value,
                "default": True,
                "is_active": True
            },
            {
                "name": DefaultOrderStatus.COMPLETE.label,
                "public_name": DefaultOrderStatus.COMPLETE.label,
                "role": OrderStatusRole.COMPLETE,
                "identifier": DefaultOrderStatus.COMPLETE.value,
                "default": True,
                "is_active": True
            },
            {
                "name": DefaultOrderStatus.CANCELED.label,
                "public_name": DefaultOrderStatus.CANCELED.label,
                "role": OrderStatusRole.CANCELED,
                "identifier": DefaultOrderStatus.CANCELED.value,
                "default": True,
                "is_active": True
            }
        ]

    def is_default(self, status_object):
        return any(s['identifier'] == status_object.identifier for s in self.default_statuses)

    def ensure_default_statuses(self):
        """
        Ensure Default Statuses.

        It is important to ensure that default
        statuses are always available. This method
        will ensure this.
        """
        # These values are based on the old Shuup data
        update_map = {
            "none": DefaultOrderStatus.NONE.value,
            "recv": DefaultOrderStatus.INITIAL.value,
            "prog": DefaultOrderStatus.PROCESSING.value,
            "comp": DefaultOrderStatus.COMPLETE.value,
            "canc": DefaultOrderStatus.CANCELED.value,
        }

        for status in OrderStatus.objects.all():
            if status.identifier not in update_map:
                continue
            status.identifier = update_map[status.identifier]
            status.save()

        for i, defaults in enumerate(self.default_statuses):
            defaults["ordering"] = i
            status = OrderStatus.objects.filter(identifier=defaults["identifier"]).first()
            if status:
                defaults.pop("name")
                defaults.pop("public_name")
                for k, v in six.iteritems(defaults):
                    setattr(status, k, v)
                status.save()
            else:
                OrderStatus.objects.create(**defaults)


class OrderQuerySet(models.QuerySet):
    def paid(self):
        return self.filter(payment_status=PaymentStatus.FULLY_PAID)

    def incomplete(self):
        return self.filter(status__role__in=(OrderStatusRole.NONE, OrderStatusRole.INITIAL, OrderStatusRole.PROCESSING))

    def complete(self):
        return self.filter(status__role=OrderStatusRole.COMPLETE)    # TODO: read status

    def valid(self):
        return self.exclude(Q(deleted=True) | Q(status__role=OrderStatusRole.CANCELED))  # TODO: read status

    def since(self, days, tz=None):
        since_date = (local_now(tz) - datetime.timedelta(days=days)).date()
        since = to_aware(since_date, tz=tz)
        return self.in_date_range(since, None)

    def in_date_range(self, start, end):
        """
        Limit to orders is given date range.

        :type start: datetime.datetime|None
        :param start: Start time, inclusive.
        :type end: datetime.datetime|None
        :param end: End time, inclusive.
        """
        result = self
        if start:
            result = result.filter(order_date__gte=to_aware(start))
        if end:
            result = result.filter(order_date__lte=to_aware(end))
        return result


@python_2_unicode_compatible
class Order(MoneyPropped, models.Model):
    # Identification
    shop = UnsavedForeignKey("Shop", on_delete=models.PROTECT, verbose_name=_('shop'))
    created_on = models.DateTimeField(auto_now_add=True, editable=False, db_index=True, verbose_name=_('created on'))
    modified_on = models.DateTimeField(auto_now=True, editable=False, db_index=True, verbose_name=_('modified on'))
    identifier = InternalIdentifierField(unique=True, db_index=True, verbose_name=_('order identifier'))
    # TODO: label is actually a choice field, need to check migrations/choice deconstruction
    label = models.CharField(max_length=32, db_index=True, verbose_name=_('label'))
    # The key shouldn't be possible to deduce (i.e. it should be random), but it is
    # not a secret. (It could, however, be used as key material for an actual secret.)
    key = models.CharField(max_length=32, unique=True, blank=False, verbose_name=_('key'))
    reference_number = models.CharField(
        max_length=64, db_index=True, unique=True, blank=True, null=True,
        verbose_name=_('reference number'))

    # Contact information
    customer = UnsavedForeignKey(
        "Contact", related_name='customer_orders', blank=True, null=True,
        on_delete=models.PROTECT,
        verbose_name=_('customer'))
    orderer = UnsavedForeignKey(
        "PersonContact", related_name='orderer_orders', blank=True, null=True,
        on_delete=models.PROTECT,
        verbose_name=_('orderer'))
    billing_address = models.ForeignKey(
        "ImmutableAddress", related_name="billing_orders",
        blank=True, null=True,
        on_delete=models.PROTECT,
        verbose_name=_('billing address'))
    shipping_address = models.ForeignKey(
        "ImmutableAddress", related_name='shipping_orders',
        blank=True, null=True,
        on_delete=models.PROTECT,
        verbose_name=_('shipping address'))
    tax_number = models.CharField(max_length=64, blank=True, verbose_name=_('tax number'))
    phone = models.CharField(max_length=64, blank=True, verbose_name=_('phone'))
    email = models.EmailField(max_length=128, blank=True, verbose_name=_('email address'))

    # Customer related information that might change after order, but is important
    # for accounting and/or reports later.
    account_manager = models.ForeignKey(
        "PersonContact", blank=True, null=True, on_delete=models.PROTECT, verbose_name=_('account manager'))
    customer_groups = models.ManyToManyField(
        "ContactGroup", related_name="customer_group_orders", verbose_name=_('customer groups'), blank=True)
    tax_group = models.ForeignKey(
        "CustomerTaxGroup", blank=True, null=True, on_delete=models.PROTECT, verbose_name=_('tax group'))

    # Status
    creator = UnsavedForeignKey(
        settings.AUTH_USER_MODEL, related_name='orders_created', blank=True, null=True,
        on_delete=models.PROTECT,
        verbose_name=_('creating user'))
    modified_by = UnsavedForeignKey(
        settings.AUTH_USER_MODEL, related_name='orders_modified', blank=True, null=True,
        on_delete=models.PROTECT,
        verbose_name=_('modifier user'))
    deleted = models.BooleanField(db_index=True, default=False, verbose_name=_('deleted'))
    status = UnsavedForeignKey("OrderStatus", verbose_name=_('status'), on_delete=models.PROTECT)
    payment_status = EnumIntegerField(
        PaymentStatus, db_index=True, default=PaymentStatus.NOT_PAID,
        verbose_name=_('payment status'))
    shipping_status = EnumIntegerField(
        ShippingStatus, db_index=True, default=ShippingStatus.NOT_SHIPPED,
        verbose_name=_('shipping status'))

    # Methods
    payment_method = UnsavedForeignKey(
        "PaymentMethod", related_name="payment_orders", blank=True, null=True,
        default=None, on_delete=models.PROTECT,
        verbose_name=_('payment method'))
    payment_method_name = models.CharField(
        max_length=100, blank=True, default="",
        verbose_name=_('payment method name'))
    payment_data = JSONField(blank=True, null=True, verbose_name=_('payment data'))

    shipping_method = UnsavedForeignKey(
        "ShippingMethod", related_name='shipping_orders',  blank=True, null=True,
        default=None, on_delete=models.PROTECT,
        verbose_name=_('shipping method'))
    shipping_method_name = models.CharField(
        max_length=100, blank=True, default="",
        verbose_name=_('shipping method name'))
    shipping_data = JSONField(blank=True, null=True, verbose_name=_('shipping data'))

    extra_data = JSONField(blank=True, null=True, verbose_name=_('extra data'))

    # Money stuff
    taxful_total_price = TaxfulPriceProperty('taxful_total_price_value', 'currency')
    taxless_total_price = TaxlessPriceProperty('taxless_total_price_value', 'currency')

    taxful_total_price_value = MoneyValueField(editable=False, verbose_name=_('grand total'), default=0)
    taxless_total_price_value = MoneyValueField(editable=False, verbose_name=_('taxless total'), default=0)
    currency = CurrencyField(verbose_name=_('currency'))
    prices_include_tax = models.BooleanField(verbose_name=_('prices include tax'))

    display_currency = CurrencyField(blank=True, verbose_name=_('display currency'))
    display_currency_rate = models.DecimalField(
        max_digits=36, decimal_places=9, default=1, verbose_name=_('display currency rate')
    )

    # Other
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('IP address'))
    # `order_date` is not `auto_now_add` for backdating purposes
    order_date = models.DateTimeField(editable=False, db_index=True, verbose_name=_('order date'))
    payment_date = models.DateTimeField(null=True, editable=False, verbose_name=_('payment date'))

    language = LanguageField(blank=True, verbose_name=_('language'))
    customer_comment = models.TextField(blank=True, verbose_name=_('customer comment'))
    admin_comment = models.TextField(blank=True, verbose_name=_('admin comment/notes'))
    require_verification = models.BooleanField(default=False, verbose_name=_('requires verification'))
    all_verified = models.BooleanField(default=False, verbose_name=_('all lines verified'))
    marketing_permission = models.BooleanField(default=False, verbose_name=_('marketing permission'))
    _codes = JSONField(blank=True, null=True, verbose_name=_('codes'))

    common_select_related = ("billing_address",)
    objects = OrderQuerySet.as_manager()

    class Meta:
        ordering = ("-id",)
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __str__(self):  # pragma: no cover
        if self.billing_address_id:
            name = self.billing_address.name
        else:
            name = "-"
        if ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS"):
            return "Order %s (%s, %s)" % (self.identifier, self.shop.name, name)
        else:
            return "Order %s (%s)" % (self.identifier, name)

    @property
    def codes(self):
        return list(self._codes or [])

    @codes.setter
    def codes(self, value):
        codes = []
        for code in value:
            if not isinstance(code, six.text_type):
                raise TypeError('Error! `codes` must be a list of strings.')
            codes.append(code)
        self._codes = codes

    def cache_prices(self):
        taxful_total = TaxfulPrice(0, self.currency)
        taxless_total = TaxlessPrice(0, self.currency)
        for line in self.lines.all().prefetch_related("taxes"):
            taxful_total += line.taxful_price
            taxless_total += line.taxless_price
        self.taxful_total_price = taxful_total
        self.taxless_total_price = taxless_total

    def _cache_contact_values(self):
        sources = [
            self.shipping_address,
            self.billing_address,
            self.customer,
            self.orderer,
        ]

        fields = ("tax_number", "email", "phone")

        for field in fields:
            if getattr(self, field, None):
                continue
            for source in sources:
                val = getattr(source, field, None)
                if val:
                    setattr(self, field, val)
                    break

        if not self.id and self.customer:
            # These fields are used for reporting and should not
            # change after create even if empty at the moment of ordering.
            self.account_manager = getattr(self.customer, "account_manager", None)
            self.tax_group = self.customer.tax_group

    def _cache_contact_values_post_create(self):
        if self.customer:
            # These fields are used for reporting and should not
            # change after create even if empty at the  moment of ordering.
            self.customer_groups.set(self.customer.groups.all())

    def _cache_values(self):
        self._cache_contact_values()

        if not self.label:
            self.label = settings.SHUUP_DEFAULT_ORDER_LABEL

        if not self.currency:
            self.currency = self.shop.currency

        if not self.prices_include_tax:
            self.prices_include_tax = self.shop.prices_include_tax

        if not self.display_currency:
            self.display_currency = self.currency
            self.display_currency_rate = 1

        if self.shipping_method_id and not self.shipping_method_name:
            self.shipping_method_name = self.shipping_method.safe_translation_getter(
                "name", default=self.shipping_method.identifier, any_language=True)

        if self.payment_method_id and not self.payment_method_name:
            self.payment_method_name = self.payment_method.safe_translation_getter(
                "name", default=self.payment_method.identifier, any_language=True)

        if not self.key:
            self.key = get_random_string(32)

        if not self.modified_by:
            self.modified_by = self.creator

    def _save_identifiers(self):
        self.identifier = "%s" % (get_order_identifier(self))
        self.reference_number = get_reference_number(self)
        super(Order, self).save(update_fields=("identifier", "reference_number",))

    def full_clean(self, exclude=None, validate_unique=True):
        self._cache_values()
        return super(Order, self).full_clean(exclude, validate_unique)

    def save(self, *args, **kwargs):
        if not self.creator_id:
            if not settings.SHUUP_ALLOW_ANONYMOUS_ORDERS:
                raise ValidationError(
                    "Error! Anonymous (userless) orders are not allowed "
                    "when `SHUUP_ALLOW_ANONYMOUS_ORDERS` is not enabled.")
        self._cache_values()
        first_save = (not self.pk)
        old_status = self.status

        if not first_save:
            old_status = Order.objects.only("status").get(pk=self.pk).status

        super(Order, self).save(*args, **kwargs)

        if first_save:  # Have to do a double save the first time around to be able to save identifiers
            self._save_identifiers()
            self._cache_contact_values_post_create()

        order_changed.send(type(self), order=self)

        if self.status != old_status:
            order_status_changed.send(type(self), order=self, old_status=old_status, new_status=self.status)

    def delete(self, using=None):
        if not self.deleted:
            self.deleted = True
            self.add_log_entry("Success! Deleted (soft).", kind=LogEntryKind.DELETION)
            # Bypassing local `save()` on purpose.
            super(Order, self).save(update_fields=("deleted", ), using=using)

    def set_canceled(self):
        if self.status.role != OrderStatusRole.CANCELED:
            self.status = OrderStatus.objects.get_default_canceled()
            self.save()

    def _set_paid(self):
        if self.payment_status != PaymentStatus.FULLY_PAID:  # pragma: no branch
            self.add_log_entry(_("Order was marked as paid."))
            self.payment_status = PaymentStatus.FULLY_PAID
            self.payment_date = local_now()
            self.save()

    def _set_partially_paid(self):
        if self.payment_status != PaymentStatus.PARTIALLY_PAID:
            self.add_log_entry(_("Order was marked as partially paid."))
            self.payment_status = PaymentStatus.PARTIALLY_PAID
            self.save()

    def is_paid(self):
        return (self.payment_status == PaymentStatus.FULLY_PAID)

    def is_partially_paid(self):
        return (self.payment_status == PaymentStatus.PARTIALLY_PAID)

    def is_deferred(self):
        return (self.payment_status == PaymentStatus.DEFERRED)

    def is_not_paid(self):
        return (self.payment_status == PaymentStatus.NOT_PAID)

    def get_total_paid_amount(self):
        amounts = self.payments.values_list('amount_value', flat=True)
        return Money(sum(amounts, Decimal(0)), self.currency)

    def get_total_unpaid_amount(self):
        difference = self.taxful_total_price.amount - self.get_total_paid_amount()
        return max(difference, Money(0, self.currency))

    def can_create_payment(self):
        zero = Money(0, self.currency)
        return not(self.is_paid() or self.is_canceled()) and self.get_total_unpaid_amount() > zero

    def create_payment(self, amount, payment_identifier=None, description=''):
        """
        Create a payment with a given amount for this order.

        If the order already has payments and sum of their amounts is
        equal or greater than `self.taxful_total_price` and the order is not
        a zero price order, an exception is raised.

        If the end sum of all payments is equal or greater than
        `self.taxful_total_price`, then the order is marked as paid.

        :param amount:
          Amount of the payment to be created.
        :type amount: Money
        :param payment_identifier:
          Identifier of the created payment. If not set, default value
          of `gateway_id:order_id:number` will be used (where `number` is
          a number of payments in the order).
        :type payment_identifier: str|None
        :param description:
          Description of the payment. Will be set to `method` property
          of the created payment.
        :type description: str

        :returns: The created Payment object
        :rtype: shuup.core.models.Payment
        """
        assert isinstance(amount, Money)
        assert amount.currency == self.currency

        payments = self.payments.order_by('created_on')

        total_paid_amount = self.get_total_paid_amount()
        if total_paid_amount >= self.taxful_total_price.amount and self.taxful_total_price:
            raise NoPaymentToCreateException(
                "Error! Order %s has already been fully paid (%s >= %s)." %
                (
                    self.pk, total_paid_amount, self.taxful_total_price
                )
            )

        if not payment_identifier:
            number = payments.count() + 1
            payment_identifier = '%d:%d' % (self.id, number)

        payment = self.payments.create(
            payment_identifier=payment_identifier,
            amount_value=amount.value,
            description=description,
        )

        if self.get_total_paid_amount() >= self.taxful_total_price.amount:
            self._set_paid()  # also calls save
        else:
            self._set_partially_paid()

        payment_created.send(sender=type(self), order=self, payment=payment)
        return payment

    def can_create_shipment(self):
        return (self.get_unshipped_products() and not self.is_canceled() and self.shipping_address)

    # TODO: Rethink either the usage of shipment parameter or renaming the method for 2.0
    @atomic
    def create_shipment(self, product_quantities, supplier=None, shipment=None):
        """
        Create a shipment for this order from `product_quantities`.
        `product_quantities` is expected to be a dict, which maps Product instances to quantities.

        Only quantities over 0 are taken into account, and if the mapping is empty or has no quantity value
        over 0, `NoProductsToShipException` will be raised.

        Orders without a shipping address defined, will raise `NoShippingAddressException`.

        :param product_quantities: a dict mapping Product instances to quantities to ship.
        :type product_quantities: dict[shuup.shop.models.Product, decimal.Decimal]
        :param supplier: Optional Supplier for this product. No validation is made.
        :param shipment: Optional unsaved Shipment for ShipmentProduct's. If not given
                         Shipment is created based on supplier parameter.
        :raises: NoProductsToShipException, NoShippingAddressException
        :return: Saved, complete Shipment object.
        :rtype: shuup.core.models.Shipment
        """
        if not product_quantities or not any(quantity > 0 for quantity in product_quantities.values()):
            raise NoProductsToShipException(
                "Error! No products to ship (`quantities` is empty or has no quantity over 0)."
            )

        if self.shipping_address is None:
            raise NoShippingAddressException("Error! Shipping address is not defined for this order.")

        assert (supplier or shipment)
        if shipment:
            assert shipment.order == self
        else:
            from ._shipments import Shipment
            shipment = Shipment(order=self, supplier=supplier)
        shipment.save()

        if not supplier:
            supplier = shipment.supplier

        supplier.module.ship_products(shipment, product_quantities)

        self.add_log_entry(_(u"Success! Shipment #%d was created.") % shipment.id)
        self.update_shipping_status()
        shipment_created.send(sender=type(self), order=self, shipment=shipment)
        shipment_created_and_processed.send(sender=type(self), order=self, shipment=shipment)
        return shipment

    def can_create_refund(self, supplier=None):
        unrefunded_amount = self.get_total_unrefunded_amount(supplier)
        unrefunded_quantity = self.get_total_unrefunded_quantity(supplier)
        return (
            (unrefunded_amount.value > 0 or unrefunded_quantity > 0)
            and not self.is_canceled()
            and not self.is_complete()
            and (self.payment_status != PaymentStatus.NOT_PAID)
        )

    def _get_tax_class_proportions(self):
        product_lines = self.lines.products()

        zero = self.lines.first().price.new(0)

        total_by_tax_class = defaultdict(lambda: zero)
        total = zero

        for line in product_lines:
            total_by_tax_class[line.product.tax_class] += line.price
            total += line.price

        if not total:
            # Can't calculate proportions, if total is zero
            return []

        return [
            (tax_class, tax_class_total / total)
            for (tax_class, tax_class_total) in total_by_tax_class.items()
        ]

    def _refund_amount(self, index, text, amount, tax_proportions, supplier=None):
        taxmod = taxing.get_tax_module()
        ctx = taxmod.get_context_from_order_source(self)
        taxes = (list(chain.from_iterable(
            taxmod.get_taxed_price(ctx, TaxfulPrice(amount * factor), tax_class).taxes
            for (tax_class, factor) in tax_proportions)))

        base_amount = amount
        if not self.prices_include_tax:
            base_amount /= (1 + sum([tax.tax.rate for tax in taxes]))
        refund_line = OrderLine.objects.create(
            text=text,
            order=self,
            type=OrderLineType.REFUND,
            ordering=index,
            base_unit_price_value=-base_amount,
            quantity=1,
            supplier=supplier
        )
        for line_tax in taxes:
            refund_line.taxes.create(
                tax=line_tax.tax,
                name=_("Refund for %s" % line_tax.name),
                amount_value=-line_tax.amount,
                base_amount_value=-line_tax.base_amount,
                ordering=1
            )
        return refund_line

    @atomic    # noqa (C901) FIXME: simply this
    def create_refund(self, refund_data, created_by=None, supplier=None):
        """
        Create a refund if passed a list of refund line data.

        Refund line data is simply a list of dictionaries where
        each dictionary contains data for a particular refund line.

        Additionally, if the parent line is of `enum` type
        `OrderLineType.PRODUCT` and the `restock_products` boolean
        flag is set to `True`, the products will be restocked with the
        exact amount set in the order supplier's `quantity` field.

        :param refund_data: List of dicts containing refund data.
        :type refund_data: [dict]
        :param created_by: Refund creator's user instance, used for
                           adjusting supplier stock.
        :type created_by: django.contrib.auth.User|None
        """
        lines = self.lines.all()
        if supplier:
            lines = lines.filter(supplier=supplier)

        index = lines.aggregate(models.Max("ordering"))["ordering__max"]
        tax_proportions = self._get_tax_class_proportions()
        zero = Money(0, self.currency)
        refund_lines = []
        total_refund_amount = zero
        available_for_refund = self.get_total_unrefunded_amount(supplier=supplier)
        product_summary = self.get_product_summary(supplier)

        for refund in refund_data:
            index += 1
            amount = refund.get("amount", zero)
            quantity = refund.get("quantity", 0)
            parent_line = refund.get("line", "amount")
            if not settings.SHUUP_ALLOW_ARBITRARY_REFUNDS and (not parent_line or parent_line == "amount"):
                raise RefundArbitraryRefundsNotAllowedException

            restock_products = refund.get("restock_products")
            refund_line = None

            assert parent_line
            assert quantity

            if parent_line == "amount":
                refund_line = self._refund_amount(
                    index, refund.get("text", _("Misc refund")), amount, tax_proportions, supplier=supplier)
            else:
                # ensure the amount to refund and the order line amount have the same signs
                if ((amount > zero and parent_line.taxful_price.amount < zero) or
                   (amount < zero and parent_line.taxful_price.amount > zero)):
                    raise InvalidRefundAmountException

                if abs(amount) > abs(parent_line.max_refundable_amount):
                    raise RefundExceedsAmountException

                # If restocking products, calculate quantity of products to restock
                product = parent_line.product

                # ensure max refundable quantity is respected for products
                if product and quantity > parent_line.max_refundable_quantity:
                    raise RefundExceedsQuantityException

                if restock_products and quantity and product:
                    from shuup.core.suppliers.enums import StockAdjustmentType
                    # restock from the unshipped quantity first
                    unshipped_quantity_to_restock = min(quantity, product_summary[product.pk]["unshipped"])
                    shipped_quantity_to_restock = min(
                        quantity - unshipped_quantity_to_restock,
                        product_summary[product.pk]["ordered"] - product_summary[product.pk]["refunded"])

                    if unshipped_quantity_to_restock > 0:
                        product_summary[product.pk]["unshipped"] -= unshipped_quantity_to_restock
                        if parent_line.supplier.stock_managed:
                            parent_line.supplier.adjust_stock(
                                product.id,
                                unshipped_quantity_to_restock,
                                created_by=created_by,
                                type=StockAdjustmentType.RESTOCK_LOGICAL)
                    if shipped_quantity_to_restock > 0 and parent_line.supplier.stock_managed:
                        parent_line.supplier.adjust_stock(
                            product.id,
                            shipped_quantity_to_restock,
                            created_by=created_by,
                            type=StockAdjustmentType.RESTOCK)
                    product_summary[product.pk]["refunded"] += quantity

                base_amount = amount if self.prices_include_tax else amount / (1 + parent_line.tax_rate)
                refund_line = OrderLine.objects.create(
                    text=_("Refund for %s" % parent_line.text),
                    order=self,
                    type=OrderLineType.REFUND,
                    parent_line=parent_line,
                    ordering=index,
                    base_unit_price_value=-(base_amount / (quantity or 1)),
                    quantity=quantity,
                    supplier=parent_line.supplier
                )
                for line_tax in parent_line.taxes.all():
                    tax_base_amount = amount / (1 + parent_line.tax_rate)
                    tax_amount = tax_base_amount * line_tax.tax.rate
                    refund_line.taxes.create(
                        tax=line_tax.tax,
                        name=_("Refund for %s" % line_tax.name),
                        amount_value=-tax_amount,
                        base_amount_value=-tax_base_amount,
                        ordering=line_tax.ordering
                    )

            total_refund_amount += refund_line.taxful_price.amount
            refund_lines.append(refund_line)

        if abs(total_refund_amount) > available_for_refund:
            raise RefundExceedsAmountException
        self.cache_prices()
        self.save()
        self.update_shipping_status()
        self.update_payment_status()
        refund_created.send(sender=type(self), order=self, refund_lines=refund_lines)

    def create_full_refund(self, restock_products=False, created_by=None):
        """
        Create a full refund for entire order content, with the option of
        restocking stocked products.

        :param restock_products: Boolean indicating whether to also restock the products.
        :param created_by: Refund creator's user instance, used for
                           adjusting supplier stock.
        :type restock_products: bool|False
        """
        if self.has_refunds():
            raise NoRefundToCreateException
        self.cache_prices()
        line_data = [{
            "line": line,
            "quantity": line.quantity,
            "amount": line.taxful_price.amount,
            "restock_products": restock_products
        } for line in self.lines.filter(quantity__gt=0) if line.type != OrderLineType.REFUND]
        self.create_refund(line_data, created_by)

    def get_total_refunded_amount(self, supplier=None):
        refunds = self.lines.refunds()
        if supplier:
            refunds = refunds.filter(
                Q(parent_line__supplier=supplier) | Q(supplier=supplier)
            )
        total = sum([line.taxful_price.amount.value for line in refunds])
        return Money(-total, self.currency)

    def get_total_unrefunded_amount(self, supplier=None):
        if supplier:
            total_refund_amount = sum([
                line.max_refundable_amount.value
                for line in self.lines.filter(supplier=supplier).exclude(type=OrderLineType.REFUND)
            ])
            arbitrary_refunds = abs(sum([
                refund_line.taxful_price.value
                for refund_line in self.lines.filter(
                    supplier=supplier, parent_line__isnull=True, type=OrderLineType.REFUND)
            ]))
            return (
                Money(max(total_refund_amount - arbitrary_refunds, 0), self.currency)
                if total_refund_amount else
                Money(0, self.currency)
            )
        return max(self.taxful_total_price.amount, Money(0, self.currency))

    def get_total_unrefunded_quantity(self, supplier=None):
        queryset = self.lines.all()
        if supplier:
            queryset = queryset.filter(supplier=supplier)
        return sum([line.max_refundable_quantity for line in queryset])

    def get_total_tax_amount(self):
        return sum(
            (line.tax_amount for line in self.lines.all()),
            Money(0, self.currency))

    def has_refunds(self):
        return self.lines.refunds().exists()

    def create_shipment_of_all_products(self, supplier=None):
        """
        Create a shipment of all the products in this Order, no matter whether or
        not any have been previously marked as shipped or not.

        See the documentation for `create_shipment`.

        :param supplier: The Supplier to use. If `None`, the first supplier in
                         the order is used. (If several are in the order, this fails.)
        :return: Saved, complete Shipment object.
        :rtype: shuup.shop.models.Shipment
        """
        from ._products import ShippingMode

        suppliers_to_product_quantities = defaultdict(lambda: defaultdict(lambda: 0))
        lines = (
            self.lines
            .filter(type=OrderLineType.PRODUCT, product__shipping_mode=ShippingMode.SHIPPED)
            .values_list("supplier_id", "product_id", "quantity"))
        for supplier_id, product_id, quantity in lines:
            if product_id:
                suppliers_to_product_quantities[supplier_id][product_id] += quantity

        if not suppliers_to_product_quantities:
            raise NoProductsToShipException("Error! Could not find any products to ship.")

        if supplier is None:
            if len(suppliers_to_product_quantities) > 1:  # pragma: no cover
                raise ValueError(
                    "Error! `create_shipment_of_all_products` can be used only when there is a single supplier."
                )
            supplier_id, quantities = suppliers_to_product_quantities.popitem()
            supplier = Supplier.objects.get(pk=supplier_id)
        else:
            quantities = suppliers_to_product_quantities[supplier.id]

        products = dict((product.pk, product) for product in Product.objects.filter(pk__in=quantities.keys()))
        quantities = dict((products[product_id], quantity) for (product_id, quantity) in quantities.items())
        return self.create_shipment(quantities, supplier=supplier)

    def check_all_verified(self):
        if not self.all_verified:
            new_all_verified = (not self.lines.filter(verified=False).exists())
            if new_all_verified:
                self.all_verified = True
                if self.require_verification:
                    self.add_log_entry(_("All rows requiring verification have been verified."))
                    self.require_verification = False
                self.save()
        return self.all_verified

    def get_purchased_attachments(self):
        from ._product_media import ProductMedia

        if self.payment_status != PaymentStatus.FULLY_PAID:
            return ProductMedia.objects.none()
        prods = self.lines.exclude(product=None).values_list("product_id", flat=True)
        return ProductMedia.objects.filter(product__in=prods, enabled=True, purchased=True)

    def get_tax_summary(self):
        """
        :rtype: taxing.TaxSummary
        """
        all_line_taxes = []
        untaxed = TaxlessPrice(0, self.currency)
        for line in self.lines.all():
            line_taxes = list(line.taxes.all())
            all_line_taxes.extend(line_taxes)
            if not line_taxes:
                untaxed += line.taxless_price
        return taxing.TaxSummary.from_line_taxes(all_line_taxes, untaxed)

    def get_product_ids_and_quantities(self, supplier=None):
        lines = self.lines.filter(type=OrderLineType.PRODUCT)
        if supplier:
            supplier_id = (supplier if isinstance(supplier, six.integer_types) else supplier.pk)
            lines = lines.filter(supplier_id=supplier_id)

        quantities = defaultdict(lambda: 0)
        for product_id, quantity in lines.values_list("product_id", "quantity"):
            quantities[product_id] += quantity
        return dict(quantities)

    def has_products(self):
        return self.lines.products().exists()

    def has_products_requiring_shipment(self, supplier=None):
        from ._products import ShippingMode
        lines = self.lines.products().filter(product__shipping_mode=ShippingMode.SHIPPED)
        if supplier:
            supplier_id = (supplier if isinstance(supplier, six.integer_types) else supplier.pk)
            lines = lines.filter(supplier_id=supplier_id)
        return lines.exists()

    def is_complete(self):
        return (self.status.role == OrderStatusRole.COMPLETE)

    def can_set_complete(self):
        return not (self.is_complete() or self.is_canceled() or bool(self.get_unshipped_products()))

    def is_fully_shipped(self):
        return (self.shipping_status == ShippingStatus.FULLY_SHIPPED)

    def is_partially_shipped(self):
        return (self.shipping_status == ShippingStatus.PARTIALLY_SHIPPED)

    def is_canceled(self):
        return (self.status.role == OrderStatusRole.CANCELED)

    def can_set_canceled(self):
        canceled = (self.status.role == OrderStatusRole.CANCELED)
        paid = self.is_paid()
        shipped = (self.shipping_status != ShippingStatus.NOT_SHIPPED)
        return not (canceled or paid or shipped)

    def update_shipping_status(self):
        status_before_update = self.shipping_status
        if not self.get_unshipped_products():
            self.shipping_status = ShippingStatus.FULLY_SHIPPED
        elif self.shipments.all_except_deleted().count():
            self.shipping_status = ShippingStatus.PARTIALLY_SHIPPED
        else:
            self.shipping_status = ShippingStatus.NOT_SHIPPED
        if status_before_update != self.shipping_status:
            self.add_log_entry(
                _("New shipping status is set to: %(shipping_status)s." % {
                    "shipping_status": self.shipping_status
                })
            )
            self.save(update_fields=("shipping_status",))

    def update_payment_status(self):
        status_before_update = self.payment_status
        if self.get_total_unpaid_amount().value == 0:
            self.payment_status = PaymentStatus.FULLY_PAID
        elif self.get_total_paid_amount().value > 0:
            self.payment_status = PaymentStatus.PARTIALLY_PAID
        elif self.payment_status != PaymentStatus.DEFERRED:   # Do not make deferred here not paid
            self.payment_status = PaymentStatus.NOT_PAID
        if status_before_update != self.payment_status:
            self.add_log_entry(
                _("New payment status is set to: %(payment_status)s." % {
                    "payment_status": self.payment_status
                })
            )
            self.save(update_fields=("payment_status",))

    def get_known_additional_data(self):
        """
        Get a list of "known additional data" in this order's `payment_data`, `shipping_data` and `extra_data`.
        The list is returned in the order the fields are specified in the settings entries for said known keys.
        `dict(that_list)` can of course be used to "flatten" the list into a dict.
        :return: list of 2-tuples.
        """
        output = []
        for data_dict, name_mapping in (
                (self.payment_data, settings.SHUUP_ORDER_KNOWN_PAYMENT_DATA_KEYS),
                (self.shipping_data, settings.SHUUP_ORDER_KNOWN_SHIPPING_DATA_KEYS),
                (self.extra_data, settings.SHUUP_ORDER_KNOWN_EXTRA_DATA_KEYS),
        ):
            if hasattr(data_dict, "get"):
                for key, display_name in name_mapping:
                    if key in data_dict:
                        output.append((force_text(display_name), data_dict[key]))
        return output

    def get_product_summary(self, supplier=None):
        """Return a dict of product IDs -> {ordered, unshipped, refunded, shipped, line_text, suppliers}"""
        supplier_id = ((supplier if isinstance(supplier, six.integer_types) else supplier.pk) if supplier else None)

        products = defaultdict(lambda: defaultdict(lambda: Decimal(0)))

        def _append_suppliers_info(product_id, supplier):
            if not products[product_id]['suppliers']:
                products[product_id]['suppliers'] = [supplier]
            elif supplier not in products[product_id]['suppliers']:
                products[product_id]['suppliers'].append(supplier)

        # Quantity for all orders
        # Note! This contains all product lines so we do not need to worry
        # about suppliers after this.
        lines = self.lines.filter(type=OrderLineType.PRODUCT)
        if supplier_id:
            lines = lines.filter(supplier_id=supplier_id)

        lines_values = lines.values_list("product_id", "text", "quantity", "supplier__name")
        for product_id, line_text, quantity, supplier_name in lines_values:
            products[product_id]['line_text'] = line_text
            products[product_id]['ordered'] += quantity
            _append_suppliers_info(product_id, supplier_name)

        # Quantity to ship
        for product_id, quantity in self._get_to_ship_quantities(supplier_id):
            products[product_id]['unshipped'] += quantity

        # Quantity shipped
        for product_id, quantity in self._get_shipped_quantities(supplier_id):
            products[product_id]['shipped'] += quantity
            products[product_id]['unshipped'] -= quantity

        # Quantity refunded
        for product_id in self._get_refunded_product_ids(supplier_id):
            refunds = self.lines.refunds().filter(parent_line__product_id=product_id)
            refunded_quantity = refunds.aggregate(total=models.Sum("quantity"))["total"] or 0
            products[product_id]["refunded"] = refunded_quantity
            products[product_id]["unshipped"] = max(products[product_id]["unshipped"] - refunded_quantity, 0)

        return products

    def _get_to_ship_quantities(self, supplier_id):
        from ._products import ShippingMode
        lines_to_ship = (
            self.lines.filter(type=OrderLineType.PRODUCT, product__shipping_mode=ShippingMode.SHIPPED))
        if supplier_id:
            lines_to_ship = lines_to_ship.filter(supplier_id=supplier_id)
        return lines_to_ship.values_list("product_id", "quantity")

    def _get_shipped_quantities(self, supplier_id):
        from ._shipments import ShipmentProduct, ShipmentStatus
        shipment_prods = (
            ShipmentProduct.objects
            .filter(shipment__order=self)
            .exclude(shipment__status=ShipmentStatus.DELETED))
        if supplier_id:
            shipment_prods = shipment_prods.filter(shipment__supplier_id=supplier_id)
        return shipment_prods.values_list("product_id", "quantity")

    def _get_refunded_product_ids(self, supplier_id):
        refunded_prods = self.lines.refunds().filter(
            type=OrderLineType.REFUND,
            parent_line__type=OrderLineType.PRODUCT)
        if supplier_id:
            refunded_prods = refunded_prods.filter(parent_line__supplier_id=supplier_id)
        return refunded_prods.distinct().values_list("parent_line__product_id", flat=True)

    def get_unshipped_products(self, supplier=None):
        return dict(
            (product, summary_datum)
            for product, summary_datum in self.get_product_summary(supplier=supplier).items()
            if summary_datum['unshipped']
        )

    def get_status_display(self):
        return force_text(self.status)

    def get_payment_method_display(self):
        return force_text(self.payment_method_name)

    def get_shipping_method_display(self):
        return force_text(self.shipping_method_name)

    def get_tracking_codes(self):
        return [shipment.tracking_code for shipment in self.shipments.all_except_deleted() if shipment.tracking_code]

    def can_edit(self):
        return (
            settings.SHUUP_ALLOW_EDITING_ORDER
            and not self.has_refunds()
            and not self.is_canceled()
            and not self.is_complete()
            and self.shipping_status == ShippingStatus.NOT_SHIPPED
            and self.payment_status == PaymentStatus.NOT_PAID
        )

    def get_customer_name(self):
        name_attrs = ["customer", "billing_address", "orderer", "shipping_address"]
        for attr in name_attrs:
            if getattr(self, "%s_id" % attr):
                return getattr(self, attr).name

    def get_available_shipping_methods(self):
        """
        Get available shipping methods.

        :rtype: list[ShippingMethod]
        """
        from shuup.core.models import ShippingMethod

        product_ids = self.lines.products().values_list("id", flat=True)
        return [
            m for m
            in ShippingMethod.objects.available(shop=self.shop, products=product_ids)
            if m.is_available_for(self)
        ]

    def get_available_payment_methods(self):
        """
        Get available payment methods.

        :rtype: list[PaymentMethod]
        """
        from shuup.core.models import PaymentMethod

        product_ids = self.lines.products().values_list("id", flat=True)
        return [
            m for m
            in PaymentMethod.objects.available(shop=self.shop, products=product_ids)
            if m.is_available_for(self)
        ]


OrderLogEntry = define_log_model(Order)
