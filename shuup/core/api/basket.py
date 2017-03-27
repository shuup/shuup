# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import exceptions, serializers, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from shuup.api.decorators import schema_serializer_class
from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.api.address import AddressSerializer
from shuup.core.basket import (
    get_basket_command_dispatcher, get_basket_order_creator
)
from shuup.core.basket.storage import BasketCompatibilityError
from shuup.core.excs import ProductNotOrderableProblem
from shuup.core.fields import (
    FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES, FORMATTED_DECIMAL_FIELD_MAX_DIGITS
)
from shuup.core.models import (
    get_company_contact, get_person_contact, MutableAddress, Order,
    OrderLineType, OrderStatus, Product, Shop, ShopProduct
)
from shuup.utils.importing import cached_load


def get_shop_id(uuid):
    try:
        return int(uuid.split("-")[0])
    except ValueError:
        raise exceptions.ValidationError("Malformed UUID")


def get_key(uuid):
    try:
        return uuid.split("-")[1]
    except (ValueError, IndexError):
        raise exceptions.ValidationError("Malformed UUID")


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


class BasketSerializer(serializers.Serializer):
    shop = serializers.SerializerMethodField()
    key = serializers.CharField(max_length=32, min_length=32)
    items = serializers.SerializerMethodField()
    unorderable_items = serializers.SerializerMethodField()
    codes = serializers.ListField()
    shipping_address = serializers.SerializerMethodField()
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

    def get_shipping_address(self, basket):
        if basket._data.get('shipping_address_id'):
            address = MutableAddress.objects.filter(id=basket._data['shipping_address_id']).first()
            return AddressSerializer(address, context=self.context).data

    def get_validation_errors(self, basket):
        return [{err.code: err.message} for err in basket.get_validation_errors()]

    def get_items(self, basket):
        return BasketLineSerializer(basket.get_final_lines(with_taxes=True), many=True, context=self.context).data

    def get_unorderable_items(self, basket):
        return BasketLineSerializer(basket.get_unorderable_lines(), many=True, context=self.context).data

    def get_shop(self, basket):
        return basket.shop.id


class BaseProductAddBasketSerializer(serializers.Serializer):
    supplier = serializers.IntegerField(required=False)
    quantity = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                        decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES,
                                        required=False)


class ShopProductAddBasketSerializer(BaseProductAddBasketSerializer):
    shop_product = serializers.PrimaryKeyRelatedField(queryset=ShopProduct.objects.all())
    shop = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()

    def get_shop(self, line):
        return line.get("shop_product").shop.pk

    def get_product(self, line):
        return line.get("shop_product").product.pk

    def validate(self, data):
        # TODO - we probably eventually want this ability
        if self.context["shop"].pk != data.get("shop_product").shop.pk:
            raise serializers.ValidationError(
                "It is not possible to add a product from a different shop in the basket.")
        return data


class ProductAddBasketSerializer(BaseProductAddBasketSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    def validate(self, data):
        # TODO - we probably eventually want this ability
        if self.context["shop"].pk != data.get("shop").pk:
            raise serializers.ValidationError(
                "It is not possible to add a product from a different shop in the basket.")
        return data


class RemoveBasketSerializer(serializers.Serializer):
    line_id = serializers.CharField()


class LineQuantitySerializer(serializers.Serializer):
    line_id = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                        decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)


class CodeAddBasketSerializer(serializers.Serializer):
    code = serializers.CharField()


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "reference_number"]


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

    def get_basket_shop(self):
        if settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
            uuid = self.kwargs.get(self.lookup_field, "")
            if uuid:
                shop_id = get_shop_id(self.kwargs.get(self.lookup_field, ""))
            else:
                # shop will be part of POST'ed data for basket creation
                shop_id = self.request.data.get("shop")
            if not shop_id:
                raise exceptions.ValidationError("No basket shop specified.")
            # this shop should be the shop associated with the basket
            return get_object_or_404(Shop, pk=shop_id)
        else:
            return Shop.objects.first()

    def process_request(self, with_basket=True):
        """
        Add context to request that's expected by basket
        """
        request = self.request._request
        user = self.request.user
        request.shop = self.get_basket_shop()
        request.person = get_person_contact(user)
        company = get_company_contact(user)
        request.customer = (company or request.person)
        if with_basket:
            request.basket = self.get_object()

    @schema_serializer_class(BasketSerializer)
    def retrieve(self, request, *args, **kwargs):
        """
        List the contents of the basket
        """
        self.process_request()
        return Response(BasketSerializer(request.basket, context=self.get_serializer_context()).data)

    def get_object(self):
        uuid = get_key(self.kwargs.get(self.lookup_field, ""))
        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")
        basket = basket_class(self.request._request, basket_name=uuid)
        try:
            basket._data = basket.storage.load(basket)
        except BasketCompatibilityError as error:
            raise exceptions.ValidationError(str(error))
        return basket

    @list_route(methods=['post'])
    def new(self, request, *args, **kwargs):
        """
        Create a brand new basket object
        """
        self.process_request(with_basket=False)
        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")
        basket = basket_class(request._request)
        if request.POST.get("customer_id"):
            from shuup.core.models import PersonContact
            customer = PersonContact.objects.get(pk=request.POST.get("customer_id"))
            request.basket.customer = customer
        stored_basket = basket.save()
        return Response(data={"uuid": "%s-%s" % (request.shop.pk, stored_basket.key)}, status=status.HTTP_201_CREATED)

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
        self.process_request()
        if "shop_product" in request.data:
            serializer = ShopProductAddBasketSerializer(data=request.data, context={"shop": request.shop})
        else:
            serializer = ProductAddBasketSerializer(data=request.data, context={"shop": request.shop})

        if serializer.is_valid():
            cmd_kwargs = {
                "request": request._request,
                "basket": request._request.basket,
                "shop_id": serializer.data.get("shop") or serializer.validated_data["shop"].pk,
                "product_id": serializer.data.get("product") or serializer.validated_data["product"].pk,
                "quantity": serializer.validated_data.get("quantity", 1),
                "supplier_id": serializer.validated_data.get("supplier")
            }
            # we call `add` directly, assuming the user will handle variations
            # as he can know all product variations easily through product API
            try:
                self._handle_cmd(request, "add", cmd_kwargs)
                request.basket.save()
            except ValidationError as exc:
                return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
            except ProductNotOrderableProblem as exc:
                return Response({"error": "{}".format(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as exc:
                return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response(BasketSerializer(request.basket, context=self.get_serializer_context()).data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(RemoveBasketSerializer)
    @detail_route(methods=['post'])
    def remove(self, request, *args, **kwargs):
        """
        Removes a basket line
        """
        self.process_request()
        serializer = RemoveBasketSerializer(data=request.data)

        if serializer.is_valid():
            cmd_kwargs = {
                "request": request._request,
                "basket": request.basket,
                "delete_{}".format(serializer.validated_data["line_id"]): 1
            }
            try:
                self._handle_cmd(request, "update", cmd_kwargs)
                request.basket.save()
            except ValidationError as exc:
                return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
            else:
                data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
                return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def clear(self, request, *args, **kwargs):
        """
        Clear basket contents
        """
        self.process_request()
        cmd_kwargs = {
            "request": request._request,
            "basket": request.basket
        }
        try:
            self._handle_cmd(request, "clear", cmd_kwargs)
            request.basket.save()
        except ValidationError as exc:
            return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
            return Response(data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def update_quantity(self, request, *args, **kwargs):
        self.process_request()
        serializer = LineQuantitySerializer(data=request.data)
        if serializer.is_valid():
            cmd_kwargs = {
                "request": request._request,
                "basket": request.basket,
                "q_{}".format(serializer.validated_data["line_id"]): serializer.validated_data["quantity"]
            }
            try:
                self._handle_cmd(request, "update", cmd_kwargs)
                request.basket.save()
            except ValidationError as exc:
                return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
            else:
                data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
                return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(CodeAddBasketSerializer)
    @detail_route(methods=['post'])
    def add_code(self, request, *args, **kwargs):
        """
        Add a campaign code to the basket
        """
        self.process_request()
        serializer = CodeAddBasketSerializer(data=request.data)

        if serializer.is_valid():
            cmd_kwargs = {
                "request": request._request,
                "basket": request.basket,
                "code": serializer.validated_data["code"]
            }
            response = self._handle_cmd(request, "add_campaign_code", cmd_kwargs)
            if response["ok"]:
                data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({"code_invalid": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(AddressSerializer)
    @detail_route(methods=['post'])
    def set_shipping_address(self, request, *args, **kwargs):
        """
        Set the shipping address of the basket.
        If ID is sent, the existing MutableAddress will be used instead.
        """
        self.process_request()

        try:
            # take the address by ID
            if request.data.get("id"):
                address = MutableAddress.objects.get(id=request.data['id'])
            else:
                serializer = AddressSerializer(data=request.data)

                if serializer.is_valid():
                    address = serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            request.basket.shipping_address = address
            request.basket.save()

        except ValidationError as exc:
            return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
        except MutableAddress.DoesNotExist:
            return Response({"error": "Address does not exist"}, status=status.HTTP_404_NOT_FOUND)
        else:
            data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
            return Response(data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def create_order(self, request, *args, **kwargs):
        self.process_request()
        request.basket.status = OrderStatus.objects.get_default_initial()
        errors = []
        for error in request.basket.get_validation_errors():
            errors.append({"code": error.code, "message": error.message})
        if len(errors):
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        order_creator = get_basket_order_creator()
        if request.POST.get("customer_id"):
            from shuup.core.models import PersonContact
            customer = PersonContact.objects.get(pk=request.POST.get("customer_id"))
            request.basket.customer = customer
        order = order_creator.create_order(request.basket)
        request.basket.finalize()
        return Response(data=OrderSerializer(order).data, status=status.HTTP_201_CREATED)
