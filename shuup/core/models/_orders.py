# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import datetime
from collections import defaultdict
from decimal import Decimal

import six
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.transaction import atomic
from django.utils.crypto import get_random_string
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from shuup.core import taxing
from shuup.core.excs import (
    NoPaymentToCreateException, NoProductsToShipException,
    NoRefundToCreateException, RefundExceedsAmountException
)
from shuup.core.fields import (
    CurrencyField, InternalIdentifierField, LanguageField, MoneyValueField,
    UnsavedForeignKey
)
from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.core.signals import refund_created, shipment_created
from shuup.utils.analog import define_log_model, LogEntryKind
from shuup.utils.money import Money
from shuup.utils.numbers import bankers_round
from shuup.utils.properties import (
    MoneyPropped, TaxfulPriceProperty, TaxlessPriceProperty
)

from ._order_lines import OrderLine, OrderLineType
from ._order_utils import get_order_identifier, get_reference_number
from ._products import Product, StockBehavior
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

    class Labels:
        NONE = _('none')
        INITIAL = _('initial')
        COMPLETE = _('complete')
        CANCELED = _('canceled')


class OrderStatusQuerySet(TranslatableQuerySet):
    def _default_for_role(self, role):
        """
        Get the default order status for the given role.

        :param role: The role to look for.
        :type role: OrderStatusRole
        :return: The OrderStatus
        :rtype: OrderStatus
        """
        try:
            return self.get(default=True, role=role)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist("No default %s OrderStatus exists." % getattr(role, "label", role))

    def get_default_initial(self):
        return self._default_for_role(OrderStatusRole.INITIAL)

    def get_default_canceled(self):
        return self._default_for_role(OrderStatusRole.CANCELED)

    def get_default_complete(self):
        return self._default_for_role(OrderStatusRole.COMPLETE)


@python_2_unicode_compatible
class OrderStatus(TranslatableModel):
    identifier = InternalIdentifierField(db_index=True, blank=False, unique=True)
    ordering = models.IntegerField(db_index=True, default=0, verbose_name=_('ordering'))
    role = EnumIntegerField(OrderStatusRole, db_index=True, default=OrderStatusRole.NONE, verbose_name=_('role'))
    default = models.BooleanField(default=False, db_index=True, verbose_name=_('default'))

    objects = OrderStatusQuerySet.as_manager()

    translations = TranslatedFields(
        name=models.CharField(verbose_name=_("name"), max_length=64)
    )

    def __str__(self):
        return self.safe_translation_getter("name", default=self.identifier)

    def save(self, *args, **kwargs):
        super(OrderStatus, self).save(*args, **kwargs)
        if self.default and self.role != OrderStatusRole.NONE:
            # If this status is the default, make the others for this role non-default.
            OrderStatus.objects.filter(role=self.role).exclude(pk=self.pk).update(default=False)


class OrderQuerySet(models.QuerySet):
    def paid(self):
        return self.filter(payment_status=PaymentStatus.FULLY_PAID)

    def incomplete(self):
        return self.filter(status__role__in=(OrderStatusRole.NONE, OrderStatusRole.INITIAL))

    def complete(self):
        return self.filter(status__role=OrderStatusRole.COMPLETE)

    def valid(self):
        return self.exclude(status__role=OrderStatusRole.CANCELED)

    def since(self, days):
        return self.filter(
            order_date__gte=datetime.datetime.combine(
                datetime.date.today() - datetime.timedelta(days=days),
                datetime.time.min
            )
        )


@python_2_unicode_compatible
class Order(MoneyPropped, models.Model):
    # Identification
    shop = UnsavedForeignKey("Shop", on_delete=models.PROTECT, verbose_name=_('shop'))
    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('created on'))
    modified_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('modified on'))
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
    tax_number = models.CharField(max_length=20, blank=True, verbose_name=_('tax number'))
    phone = models.CharField(max_length=64, blank=True, verbose_name=_('phone'))
    email = models.EmailField(max_length=128, blank=True, verbose_name=_('email address'))

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
    # order_date is not `auto_now_add` for backdating purposes
    order_date = models.DateTimeField(editable=False, verbose_name=_('order date'))
    payment_date = models.DateTimeField(null=True, editable=False, verbose_name=_('payment date'))

    language = LanguageField(blank=True, verbose_name=_('language'))
    customer_comment = models.TextField(blank=True, verbose_name=_('customer comment'))
    admin_comment = models.TextField(blank=True, verbose_name=_('admin comment/notes'))
    require_verification = models.BooleanField(default=False, verbose_name=_('requires verification'))
    all_verified = models.BooleanField(default=False, verbose_name=_('all lines verified'))
    marketing_permission = models.BooleanField(default=True, verbose_name=_('marketing permission'))
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
        if settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
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
                raise TypeError('codes must be a list of strings')
            codes.append(code)
        self._codes = codes

    def cache_prices(self):
        taxful_total = TaxfulPrice(0, self.currency)
        taxless_total = TaxlessPrice(0, self.currency)
        for line in self.lines.all():
            taxful_total += _round_price(line.taxful_price)
            taxless_total += _round_price(line.taxless_price)
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
                    "Anonymous (userless) orders are not allowed "
                    "when SHUUP_ALLOW_ANONYMOUS_ORDERS is not enabled.")
        self._cache_values()
        first_save = (not self.pk)
        super(Order, self).save(*args, **kwargs)
        if first_save:  # Have to do a double save the first time around to be able to save identifiers
            self._save_identifiers()
        for line in self.lines.exclude(product_id=None):
            line.supplier.module.update_stock(line.product_id)

    def delete(self, using=None):
        if not self.deleted:
            self.deleted = True
            self.add_log_entry("Deleted.", kind=LogEntryKind.DELETION)
            # Bypassing local `save()` on purpose.
            super(Order, self).save(update_fields=("deleted", ), using=using)

    def set_canceled(self):
        if self.status.role != OrderStatusRole.CANCELED:
            self.status = OrderStatus.objects.get_default_canceled()
            self.save()

    def _set_paid(self):
        if self.payment_status != PaymentStatus.FULLY_PAID:  # pragma: no branch
            self.add_log_entry(_('Order marked as paid.'))
            self.payment_status = PaymentStatus.FULLY_PAID
            self.payment_date = now()
            self.save()

    def _set_partially_paid(self):
        if self.payment_status != PaymentStatus.PARTIALLY_PAID:
            self.add_log_entry(_('Order marked as partially paid.'))
            self.payment_status = PaymentStatus.PARTIALLY_PAID
            self.save()

    def is_paid(self):
        return (self.payment_status == PaymentStatus.FULLY_PAID)

    def get_total_paid_amount(self):
        amounts = self.payments.values_list('amount_value', flat=True)
        return Money(sum(amounts, Decimal(0)), self.currency)

    def get_total_unpaid_amount(self):
        difference = self.taxful_total_price.amount - self.get_total_paid_amount()
        return max(difference, Money(0, self.currency))

    def can_create_payment(self):
        return not(self.is_paid() or self.is_canceled() or (self.has_refunds() and not self.can_create_refund()))

    def create_payment(self, amount, payment_identifier=None, description=''):
        """
        Create a payment with given amount for this order.

        If the order already has payments and sum of their amounts is
        equal or greater than self.taxful_total_price, an exception is raised.

        If the end sum of all payments is equal or greater than
        self.taxful_total_price, then the order is marked as paid.

        :param amount:
          Amount of the payment to be created
        :type amount: Money
        :param payment_identifier:
          Identifier of the created payment. If not set, default value
          of "gateway_id:order_id:number" will be used (where number is
          number of payments in the order).
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
        if total_paid_amount >= self.taxful_total_price.amount:
            raise NoPaymentToCreateException(
                "Order %s has already been fully paid (%s >= %s)." %
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

        return payment

    def can_create_shipment(self):
        return (self.get_unshipped_products() and not self.is_canceled())

    @atomic
    def create_shipment(self, product_quantities, supplier=None, shipment=None):
        """
        Create a shipment for this order from `product_quantities`.
        `product_quantities` is expected to be a dict mapping Product instances to quantities.

        Only quantities over 0 are taken into account, and if the mapping is empty or has no quantity value
        over 0, `NoProductsToShipException` will be raised.

        :param product_quantities: a dict mapping Product instances to quantities to ship
        :type product_quantities: dict[shuup.shop.models.Product, decimal.Decimal]
        :param supplier: Optional Supplier for this product. No validation is made
                         as to whether the given supplier supplies the products.
        :param shipment: Optional unsaved Shipment for ShipmentProduct's. If not given
                         Shipment is created based on supplier parameter.
        :raises: NoProductsToShipException
        :return: Saved, complete Shipment object
        :rtype: shuup.core.models.Shipment
        """
        if not product_quantities or not any(quantity > 0 for quantity in product_quantities.values()):
            raise NoProductsToShipException("No products to ship (`quantities` is empty or has no quantity over 0).")

        assert (supplier or shipment)
        if shipment:
            assert shipment.order == self

        from ._shipments import ShipmentProduct
        if not shipment:
            from ._shipments import Shipment
            shipment = Shipment(order=self, supplier=supplier)
        shipment.save()

        for product, quantity in product_quantities.items():
            if quantity > 0:
                sp = ShipmentProduct(shipment=shipment, product=product, quantity=quantity)
                sp.cache_values()
                sp.save()

        shipment.cache_values()
        shipment.save()

        self.add_log_entry(_(u"Shipment #%d created.") % shipment.id)
        self.update_shipping_status()
        shipment_created.send(sender=type(self), order=self, shipment=shipment)
        return shipment

    def can_create_refund(self):
        return (self.taxful_total_price.amount.value > 0 and not self.can_edit())

    @atomic
    def create_refund(self, refund_data, created_by=None):
        """
        Create a refund if passed a list of refund line data.

        Refund line data is simply a list of dictionaries where
        each dictionary contains data for a particular refund line.

        Additionally, if the parent line is of enum type
        `OrderLineType.PRODUCT` and the `restock_products` boolean
        flag is set to `True`, the products will be restocked with the
        order's supplier the exact amount of the value of the `quantity`
        field.

        If data for a refund line includes both an amount and a
        quantity to refund, creates a separate refund line for each
        refund type.

        :param refund_data: List of dicts containing refund data.
        :type refund_data: [dict]
        :param created_by: Refund creator's user instance, used for
                           adjusting supplier stock.
        :type created_by: django.contrib.auth.User|None
        """
        index = self.lines.all().aggregate(models.Max("ordering"))["ordering__max"]
        zero = Money(0, self.currency)
        refund_lines = []
        for refund in refund_data:
            index += 1
            amount = refund.get("amount", zero)
            quantity = refund.get("quantity", 0)
            parent_line = refund.get("line")
            restock_products = refund.get("restock_products")
            refund_line = None
            percent_refunded = 0

            assert parent_line
            # TODO: Also raise this if the sum amount of refunds exceeds total,
            #       order amount, and do so before creating any order lines
            self.cache_prices()
            if amount > self.taxful_total_price.amount:
                raise RefundExceedsAmountException

            # If restocking products, calculate quantity of products to restock
            product = parent_line.product
            if (restock_products and quantity and product and (product.stock_behavior == StockBehavior.STOCKED)):
                from shuup.core.suppliers.enums import StockAdjustmentType

                shipped_quantity = parent_line.shipped_quantity
                refunded_quantity = parent_line.refunded_quantity
                restockable_quantity = shipped_quantity - refunded_quantity
                quantity_to_restock = min(quantity, restockable_quantity)

                if quantity_to_restock > 0:
                    parent_line.supplier.adjust_stock(
                        product.id, quantity_to_restock, created_by=created_by, type=StockAdjustmentType.RESTOCK)

            # If a quantity provided, add a separate refund line
            if quantity:
                unit_price = parent_line.discounted_unit_price.amount
                refund_line = OrderLine.objects.create(
                    text=_("Refund for %s" % parent_line.text),
                    order=self,
                    type=OrderLineType.QUANTITY_REFUND,
                    parent_line=parent_line,
                    ordering=index,
                    base_unit_price_value=-unit_price,
                    quantity=quantity,
                )
                percent_refunded = quantity / parent_line.quantity
                refund_lines.append(refund_line)

            # If amount is provided, add a separate refund line
            if amount:
                refund_line = OrderLine.objects.create(
                    text=_("Refund for %s" % parent_line.text),
                    order=self,
                    type=OrderLineType.AMOUNT_REFUND,
                    parent_line=parent_line,
                    ordering=index,
                    base_unit_price_value=-amount,
                    quantity=1
                )
                percent_refunded = amount / parent_line.price
                refund_lines.append(refund_line)

            if refund_line:
                for line_tax in parent_line.taxes.all():
                    refund_line.taxes.create(
                        tax=line_tax.tax,
                        name=_("Refund for %s" % line_tax.name),
                        amount_value=-line_tax.amount_value * percent_refunded,
                        base_amount_value=-line_tax.base_amount_value * percent_refunded,
                        ordering=line_tax.ordering
                    )

        self.cache_prices()
        self.save()
        self.update_shipping_status()
        refund_created.send(sender=type(self), order=self, refund_lines=refund_lines)

    def create_full_refund(self, restock_products=False):
        """
        Create a full for entire order contents, with the option of
        restocking stocked products.

        :param restock_products: Boolean indicating whether to restock products
        :type restock_products: bool|False
        """
        if self.has_refunds():
            raise NoRefundToCreateException
        self.cache_prices()
        line_data = [
            {"line": line, "quantity": line.quantity, "restock_products": restock_products}
            for line in self.lines.all()
            if (line.taxful_price or (line.type == OrderLineType.PRODUCT))
        ]
        self.create_refund(line_data)

    def get_total_refunded_amount(self):
        total = sum(line.taxful_price.amount.value for line in self.lines.refunds())
        return Money(-total, self.currency)

    def get_total_unrefunded_amount(self):
        return max(self.taxful_total_price.amount, Money(0, self.currency))

    def has_refunds(self):
        return self.lines.refunds().exists()

    def create_shipment_of_all_products(self, supplier=None):
        """
        Create a shipment of all the products in this Order, no matter whether or not any have been previously
        marked as shipped or not.

        See the documentation for `create_shipment`.

        :param supplier: The Supplier to use. If `None`, the first supplier in
                         the order is used. (If several are in the order, this fails.)
        :return: Saved, complete Shipment object
        :rtype: shuup.shop.models.Shipment
        """
        suppliers_to_product_quantities = defaultdict(lambda: defaultdict(lambda: 0))
        lines = (
            self.lines
            .filter(type=OrderLineType.PRODUCT)
            .values_list("supplier_id", "product_id", "quantity"))
        for supplier_id, product_id, quantity in lines:
            if product_id:
                suppliers_to_product_quantities[supplier_id][product_id] += quantity

        if not suppliers_to_product_quantities:
            raise NoProductsToShipException("Could not find any products to ship.")

        if supplier is None:
            if len(suppliers_to_product_quantities) > 1:  # pragma: no cover
                raise ValueError("Can only use create_shipment_of_all_products when there is only one supplier")
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
                    self.add_log_entry(_('All rows requiring verification have been verified.'))
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

    def get_product_ids_and_quantities(self):
        quantities = defaultdict(lambda: 0)
        for product_id, quantity in self.lines.filter(type=OrderLineType.PRODUCT).values_list("product_id", "quantity"):
            quantities[product_id] += quantity
        return dict(quantities)

    def is_complete(self):
        return (self.status.role == OrderStatusRole.COMPLETE)

    def can_set_complete(self):
        fully_shipped = (self.shipping_status == ShippingStatus.FULLY_SHIPPED)
        canceled = (self.status.role == OrderStatusRole.CANCELED)
        return (not self.is_complete()) and fully_shipped and (not canceled)

    def is_canceled(self):
        return (self.status.role == OrderStatusRole.CANCELED)

    def can_set_canceled(self):
        canceled = (self.status.role == OrderStatusRole.CANCELED)
        paid = self.is_paid()
        shipped = (self.shipping_status != ShippingStatus.NOT_SHIPPED)
        return not (canceled or paid or shipped)

    def update_shipping_status(self):
        if self.shipping_status == ShippingStatus.FULLY_SHIPPED:
            return

        if not self.get_unshipped_products():
            self.shipping_status = ShippingStatus.FULLY_SHIPPED
            self.add_log_entry(_(u"All products have been shipped. Fully Shipped status set."))
            self.save(update_fields=("shipping_status",))
        elif self.shipments.count():
            self.shipping_status = ShippingStatus.PARTIALLY_SHIPPED
            self.save(update_fields=("shipping_status",))

    def get_known_additional_data(self):
        """
        Get a list of "known additional data" in this order's payment_data, shipping_data and extra_data.
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

    def get_product_summary(self):
        """Return a dict of product IDs -> {ordered, unshipped, refunded, shipped}"""

        products = defaultdict(lambda: defaultdict(lambda: Decimal(0)))
        lines = (
            self.lines.filter(type=OrderLineType.PRODUCT)
            .values_list("product_id", "quantity"))
        for product_id, quantity in lines:
            products[product_id]['ordered'] += quantity
            products[product_id]['unshipped'] += quantity

        from ._shipments import ShipmentProduct

        shipment_prods = (
            ShipmentProduct.objects
            .filter(shipment__order=self)
            .values_list("product_id", "quantity"))
        for product_id, quantity in shipment_prods:
            products[product_id]['shipped'] += quantity
            products[product_id]['unshipped'] -= quantity

        refunded_prods = self.lines.refunds().filter(
            type=OrderLineType.QUANTITY_REFUND,
            parent_line__type=OrderLineType.PRODUCT
        ).distinct().values_list("parent_line__product_id", flat=True)
        for product_id in refunded_prods:
            refunds = self.lines.refunds().filter(parent_line__product_id=product_id)
            refunded_quantity = refunds.aggregate(total=models.Sum("quantity"))["total"] or 0
            products[product_id]["refunded"] = refunded_quantity
            products[product_id]["unshipped"] = max(products[product_id]["unshipped"] - refunded_quantity, 0)

        return products

    def get_unshipped_products(self):
        return dict(
            (product, summary_datum)
            for product, summary_datum in self.get_product_summary().items()
            if summary_datum['unshipped']
        )

    def get_status_display(self):
        return force_text(self.status)

    def get_tracking_codes(self):
        return [shipment.tracking_code for shipment in self.shipments.all() if shipment.tracking_code]

    def can_edit(self):
        return (
            not self.has_refunds() and
            not self.is_canceled() and
            not self.is_complete() and
            self.shipping_status == ShippingStatus.NOT_SHIPPED and
            self.payment_status == PaymentStatus.NOT_PAID
        )


OrderLogEntry = define_log_model(Order)


def _round_price(value):
    return bankers_round(value, 2)  # TODO: To be fixed in SHUUP-1912
