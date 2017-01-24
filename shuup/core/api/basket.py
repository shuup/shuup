# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from uuid import uuid1

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from shuup.api.decorators import schema_serializer_class
from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.excs import ProductNotOrderableProblem
from shuup.core.fields import (
    FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES, FORMATTED_DECIMAL_FIELD_MAX_DIGITS
)
from shuup.core.models import OrderLineType, Product
from shuup.core.basket import get_basket_command_dispatcher
from shuup.utils.importing import cached_load


class BasketProductSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Product)

    class Meta:
        model = Product
        fields = ["id", "translations"]


class BasketLineSerializer(serializers.Serializer):
    product = BasketProductSerializer(required=False)
    image = serializers.SerializerMethodField()
    text = serializers.CharField()
    sku = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                        decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                     decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    base_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                          decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    discount_amount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                               decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    type = EnumField(OrderLineType)
    shop = serializers.SerializerMethodField()
    shop_product = serializers.SerializerMethodField()
    line_id = serializers.CharField()

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

    def get_shop_product(self, line):
        return line.shop_product.id if line.product else None

    def get_shop(self, line):
        return line.shop.id if line.shop else None


class BasketUUIDSerializer(serializers.Serializer):
    uuid = serializers.CharField()


class BasketSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=32, min_length=32)
    items = serializers.SerializerMethodField()
    unorderable_items = serializers.SerializerMethodField()
    codes = serializers.ListField()
    shipping_method = serializers.IntegerField()
    payment_method = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                           decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    total_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                           decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxful_total_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                  decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxless_total_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                   decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    total_discount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                              decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxful_total_discount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                     decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxless_total_discount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                      decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    total_price_of_products = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                       decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    validation_errors = serializers.SerializerMethodField()

    def get_validation_errors(self, basket):
        return [{err.code: err.message} for err in basket.get_validation_errors()]

    def get_items(self, basket):
        return BasketLineSerializer(basket.get_final_lines(with_taxes=True), many=True, context=self.context).data

    def get_unorderable_items(self, basket):
        return BasketLineSerializer(basket.get_unorderable_lines(), many=True, context=self.context).data


class ProductAddBasketSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    shop = serializers.IntegerField()
    supplier = serializers.IntegerField(required=False)
    quantity = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                        decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES,
                                        required=False)


class RemoveBasketSerializer(serializers.Serializer):
    line_id = serializers.CharField()


class CodeAddBasketSerializer(serializers.Serializer):
    code = serializers.CharField()


class BasketViewSet(PermissionHelperMixin, viewsets.ViewSet):
    """
    This class contains all methods to manage the request basket.

    The endpoints just forward commands to the configured `BasketCommandDispatcher`
    assuming it has the following ones:

    - `add` - to add a shop product
    - `update` - to update/remove an order line
        (the expected kwargs should be q_ to update and remove_ to delete a line)
    - `clean` - remove all lines and codes from the basket
    - `add_campaign_code` - add a coupon code to the basket

    """

    # just to make use of the convinient ViewSet class
    queryset = Product.objects.none()
    lookup_field = "uuid"

    def get_view_name(self):
        return _("Basket")

    @classmethod
    def get_help_text(cls):
        return _("Basket items can be listed, added, removed and cleaned. Also campaign codes can be added.")

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    @schema_serializer_class(BasketSerializer)
    def retrieve(self, request, *args, **kwargs):
        """
        List the contents of the basket
        """
        basket = self.get_object()
        return Response(BasketSerializer(basket, context=self.get_serializer_context()).data)

    def get_object(self):
        uuid = self.kwargs[self.lookup_field]
        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")
        basket = basket_class(self.request._request, key=uuid)
        basket._load()
        return basket

    @list_route(methods=['post'])
    def new(self, request, *args, **kwargs):
        """
        Create a brand new basket object
        """

        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")
        basket_uuid = uuid1().hex
        basket = basket_class(request, key=basket_uuid)
        basket.save()
        return Response(data={"uuid": basket_uuid}, status=status.HTTP_201_CREATED)

    def _handle_cmd(self, request, command, kwargs):
        cmd_dispatcher = get_basket_command_dispatcher(request)
        cmd_handler = cmd_dispatcher.get_command_handler(command)
        cmd_kwargs = cmd_dispatcher.preprocess_kwargs(command, kwargs)
        response = cmd_handler(**cmd_kwargs)
        return cmd_dispatcher.postprocess_response(command, cmd_kwargs, response)

    @schema_serializer_class(ProductAddBasketSerializer)
    @detail_route(methods=['post'])
    def add(self, request, *args, **kwargs):
        """
        Adds a product to the basket
        """
        basket = self.get_object()
        serializer = ProductAddBasketSerializer(data=request.data)

        if serializer.is_valid():
            cmd_kwargs = {
                "request": request,
                "basket": basket,
                "shop_id": serializer.validated_data["shop"],
                "product_id": serializer.validated_data["product"],
                "quantity": serializer.validated_data.get("quantity", 1),
                "supplier_id": serializer.validated_data.get("supplier")
            }
            # we call `add` directly, assuming the user will handle variations
            # as he can know all product variations easily through product API
            try:
                response = self._handle_cmd(request, "add", cmd_kwargs)
                basket.save()
            except ValidationError as exc:
                return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
            except ProductNotOrderableProblem as exc:
                return Response({"error": "{}".format(exc)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(response, status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(RemoveBasketSerializer)
    @detail_route(methods=['post'])
    def remove(self, request, *args, **kwargs):
        """
        Removes a basket line
        """
        basket = self.get_object()
        serializer = RemoveBasketSerializer(data=request.data)

        if serializer.is_valid():
            cmd_kwargs = {
                "request": request,
                "basket": basket,
                "delete_{}".format(serializer.validated_data["line_id"]): 1
            }
            try:
                response = self._handle_cmd(request, "update", cmd_kwargs)
            except ValidationError as exc:
                return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(response, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def clear(self, request, *args, **kwargs):
        """
        Clear basket contents
        """
        basket = self.get_object()
        cmd_kwargs = {
            "request": request,
            "basket": basket
        }
        try:
            response = self._handle_cmd(request, "clear", cmd_kwargs)
        except ValidationError as exc:
            return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(response, status=status.HTTP_204_NO_CONTENT)

    @schema_serializer_class(CodeAddBasketSerializer)
    @detail_route(methods=['post'])
    def add_code(self, request, *args, **kwargs):
        """
        Add a campaign code to the basket
        """
        basket = self.get_object()
        serializer = CodeAddBasketSerializer(data=request.data)

        if serializer.is_valid():
            cmd_kwargs = {
                "request": request,
                "basket": basket,
                "code": serializer.validated_data["code"]
            }
            try:
                response = self._handle_cmd(request, "add_campaign_code", cmd_kwargs)
            except ValidationError as exc:
                return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(response, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
