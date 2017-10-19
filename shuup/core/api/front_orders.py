# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, serializers, viewsets

from shuup.api.mixins import PermissionHelperMixin
from shuup.core.api.address import AddressSerializer
from shuup.core.api.orders import OrderFilter
from shuup.core.models import get_person_contact, Order, OrderLine, Shop

from .mixins import BaseLineSerializerMixin, BaseOrderTotalSerializerMixin


class ShopSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    contact_address = AddressSerializer()
    options = serializers.JSONField(binary=False, required=False)

    class Meta:
        model = Shop
        fields = ("id", "name", "logo", "options", "contact_address")

    def get_logo(self, shop):
        if shop.logo:
            return self.context["request"].build_absolute_uri(shop.logo.url)


class OrderLineSerializer(BaseLineSerializerMixin, serializers.ModelSerializer):
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


class OrderSerializer(BaseOrderTotalSerializerMixin, serializers.ModelSerializer):
    shop = ShopSerializer()

    class Meta:
        model = Order
        fields = "__all__"


class OrderDetailSerializer(BaseOrderTotalSerializerMixin, serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True)

    class Meta:
        model = Order
        fields = "__all__"


class FrontOrderViewSet(PermissionHelperMixin,
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
