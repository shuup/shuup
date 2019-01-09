# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, serializers, viewsets

from shuup.api.mixins import PermissionHelperMixin
from shuup.core.api.address import AddressSerializer
from shuup.core.api.orders import (
    OrderFilter, OrderTaxesMixin, PaymentSerializer
)
from shuup.core.api.serializers import LabelSerializer
from shuup.core.api.service import (
    PaymentMethodSerializer, ShippingMethodSerializer
)
from shuup.core.api.shop import CurrencySerializer
from shuup.core.models import (
    Currency, get_person_contact, Order, OrderLine, Shop
)
from shuup.core.pricing import TaxfulPrice, TaxlessPrice

from .mixins import (
    BaseLineSerializerMixin, BaseOrderTotalSerializerMixin,
    TaxLineSerializerMixin
)


def filter_products_lines(line):
    return line.product


def sum_order_lines_price(order, attribute, filter_line_fn=None):
    """
    Calculate the totals same way as for orders which is from rounded
    line prices.

    :param order The order
    :type order shuup.Order

    :param attribute The attribute to sum
    :type attribute string

    :param filter_line_fn A callable to filter the line,
                          must return `True` if the line should be considered
    :type filter_line_fn callable
    """
    if "taxful" in attribute:
        taxful = True
    elif "taxless" in attribute:
        taxful = False
    else:
        taxful = order.prices_include_tax

    zero = (TaxfulPrice if taxful else TaxlessPrice)(0, order.currency)
    return sum([getattr(x, attribute) for x in order.lines.all() if (not filter_line_fn or filter_line_fn(x))], zero)


class OrderShopSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    contact_address = AddressSerializer()
    options = serializers.JSONField(binary=False, required=False)
    labels = LabelSerializer(many=True)

    class Meta:
        model = Shop
        fields = (
            "id", "name", "description", "short_description",
            "logo", "options", "contact_address", "labels"
        )

    def get_logo(self, shop):
        if shop.logo:
            return self.context["request"].build_absolute_uri(shop.logo.url)


class OrderLineSerializer(BaseLineSerializerMixin, TaxLineSerializerMixin, serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    gross_weight = serializers.ReadOnlyField(source="product.gross_weight")
    net_weight = serializers.ReadOnlyField(source="product.net_weight")

    class Meta:
        model = OrderLine
        fields = "__all__"

    def get_image(self, line):
        """ Return simply the primary image URL """

        if not line.product:
            return

        primary_image = line.product.primary_image

        # no image found
        if not primary_image:
            # check for variation parent image
            if not line.product.variation_parent or not line.product.variation_parent.primary_image:
                return

            primary_image = line.product.variation_parent.primary_image

        if primary_image.external_url:
            return primary_image.external_url
        else:
            return self.context["request"].build_absolute_uri(primary_image.file.url)


class OrderSumTotalSerializerMixin(serializers.Serializer):
    taxful_total_discount = serializers.SerializerMethodField()
    taxless_total_discount = serializers.SerializerMethodField()
    total_price_of_products = serializers.SerializerMethodField()
    taxful_total_price_of_products = serializers.SerializerMethodField()
    taxless_total_price_of_products = serializers.SerializerMethodField()

    def get_taxful_total_discount(self, order):
        return Decimal(sum_order_lines_price(order, "taxful_discount_amount"))

    def get_taxless_total_discount(self, order):
        return Decimal(sum_order_lines_price(order, "taxless_discount_amount"))

    def get_total_price_of_products(self, order):
        return Decimal(sum_order_lines_price(order, "price", filter_products_lines))

    def get_taxful_total_price_of_products(self, order):
        return Decimal(sum_order_lines_price(order, "taxful_price", filter_products_lines))

    def get_taxless_total_price_of_products(self, order):
        return Decimal(sum_order_lines_price(order, "taxless_price", filter_products_lines))


class BaseOrderSerializer(serializers.Serializer):
    currency = serializers.SerializerMethodField()
    shipping_address = AddressSerializer()
    billing_address = AddressSerializer()
    payment_method = PaymentMethodSerializer()
    shipping_method = ShippingMethodSerializer()

    def get_currency(self, order):
        return CurrencySerializer(Currency.objects.get(code=order.currency), context=self.context).data


class OrderSerializer(BaseOrderTotalSerializerMixin,
                      OrderSumTotalSerializerMixin,
                      BaseOrderSerializer,
                      serializers.ModelSerializer):
    shop = OrderShopSerializer()
    payments = PaymentSerializer(many=True)

    class Meta:
        model = Order
        fields = "__all__"


class OrderDetailSerializer(BaseOrderTotalSerializerMixin,
                            OrderSumTotalSerializerMixin,
                            BaseOrderSerializer,
                            serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True)
    payments = PaymentSerializer(many=True)

    class Meta:
        model = Order
        fields = "__all__"


class FrontOrderViewSet(OrderTaxesMixin,
                        PermissionHelperMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = OrderFilter

    def get_view_name(self):
        return _("Front Orders")

    def get_serializer_class(self):
        if self.action == "list":
            return OrderSerializer
        else:
            return OrderDetailSerializer

    @classmethod
    def get_help_text(cls):
        return _("Retrieve and list the current users orders.")

    def get_queryset(self):
        return self.queryset.filter(customer=get_person_contact(self.request.user))
