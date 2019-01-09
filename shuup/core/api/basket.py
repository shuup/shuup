# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import exceptions, serializers, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from shuup.api.decorators import schema_serializer_class
from shuup.api.fields import EnumField, FormattedDecimalField
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.api.address import AddressSerializer
from shuup.core.api.contacts import PersonContactSerializer
from shuup.core.api.tax import SourceLineTaxSerializer, TaxSummarySerializer
from shuup.core.basket import (
    get_basket_command_dispatcher, get_basket_order_creator
)
from shuup.core.basket.storage import BasketCompatibilityError, get_storage
from shuup.core.excs import ProductNotOrderableProblem
from shuup.core.models import (
    AnonymousContact, Basket, Contact, Currency, get_company_contact,
    get_person_contact, MutableAddress, Order, OrderLineType, OrderStatus,
    PaymentMethod, Product, ShippingMethod, Shop, ShopProduct, ShopStatus
)
from shuup.utils.importing import cached_load

from .mixins import (
    BaseLineSerializerMixin, BaseOrderTotalSerializerMixin,
    TaxLineSerializerMixin
)
from .service import PaymentMethodSerializer, ShippingMethodSerializer
from .shop import CurrencySerializer


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


class NewBasketSerializer(serializers.Serializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.filter(status=ShopStatus.ENABLED), required=False)
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.filter(is_active=True), allow_null=True, required=False)
    orderer = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.filter(is_active=True), allow_null=True, required=False)


class BasketSetCustomerSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.filter(is_active=True), allow_null=True)
    orderer = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.filter(is_active=True), allow_null=True, required=False)


class BasketRequestAbandonedSerializer(serializers.Serializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.filter(status=ShopStatus.ENABLED))
    days_ago = serializers.IntegerField(required=False)
    not_updated_in_hours = serializers.IntegerField(required=False)


class BasketCustomerSerializer(PersonContactSerializer):
    default_shipping_address = serializers.PrimaryKeyRelatedField(read_only=True)
    default_billing_address = serializers.PrimaryKeyRelatedField(read_only=True)
    user = serializers.SerializerMethodField()

    class Meta(PersonContactSerializer.Meta):
        exclude = None
        fields = [
            "id",
            "user",
            "name",
            "email",
            "first_name",
            "last_name",
            "phone",
            "default_shipping_method",
            "default_payment_method",
            "default_shipping_address",
            "default_billing_address"
        ]

    def get_user(self, customer):
        user = getattr(customer, 'user', None)
        if user:
            return getattr(user, 'pk', None)


class BasketBaseLineSerializer(BaseLineSerializerMixin, serializers.Serializer):
    product = BasketProductSerializer(required=False)
    image = serializers.SerializerMethodField()
    text = serializers.CharField()
    sku = serializers.CharField()
    can_delete = serializers.BooleanField()
    can_change_quantity = serializers.BooleanField()
    supplier = serializers.IntegerField(source="supplier.id")

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


class BasketLineSerializer(TaxLineSerializerMixin, BasketBaseLineSerializer):
    pass


class BasketUnorderableLineSerializer(BasketBaseLineSerializer):
    pass


class BasketSerializer(BaseOrderTotalSerializerMixin, serializers.Serializer):
    shop = serializers.SerializerMethodField()
    key = serializers.CharField(max_length=32, min_length=32)
    items = serializers.SerializerMethodField()
    unorderable_items = serializers.SerializerMethodField()
    codes = serializers.ListField()
    shipping_address = serializers.SerializerMethodField()
    shipping_method = ShippingMethodSerializer()
    payment_method = PaymentMethodSerializer()
    available_shipping_methods = serializers.SerializerMethodField()
    available_payment_methods = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    validation_errors = serializers.SerializerMethodField()
    customer_comment = serializers.SerializerMethodField()

    total_discount = FormattedDecimalField()
    total_price = FormattedDecimalField()
    taxful_total_discount = FormattedDecimalField()
    taxless_total_discount = FormattedDecimalField()
    total_price_of_products = FormattedDecimalField()
    taxful_total_price_of_products = FormattedDecimalField()
    taxless_total_price_of_products = FormattedDecimalField()

    prices_include_tax = serializers.BooleanField()
    currency = serializers.SerializerMethodField()

    def get_customer(self, basket):
        if basket.customer:
            return BasketCustomerSerializer(basket.customer).data

    def get_currency(self, basket):
        return CurrencySerializer(Currency.objects.get(code=basket.currency), context=self.context).data

    def get_shipping_address(self, basket):
        if basket._data.get('shipping_address_id'):
            address = MutableAddress.objects.filter(id=basket._data['shipping_address_id']).first()
            return AddressSerializer(address, context=self.context).data

    def get_validation_errors(self, basket):
        return [{err.code: "%s" % err.message} for err in basket.get_validation_errors()]

    def get_items(self, basket):
        return BasketLineSerializer(basket.get_final_lines(with_taxes=True), many=True, context=self.context).data

    def get_unorderable_items(self, basket):
        return BasketUnorderableLineSerializer(basket.get_unorderable_lines(), many=True, context=self.context).data

    def get_shop(self, basket):
        return basket.shop.id

    def get_available_payment_methods(self, basket):
        return PaymentMethodSerializer(basket.get_available_payment_methods(), many=True, context=self.context).data

    def get_available_shipping_methods(self, basket):
        return ShippingMethodSerializer(basket.get_available_shipping_methods(), many=True, context=self.context).data

    def get_customer_comment(self, basket):
        return basket.customer_comment or ""


class StoredBasketSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Basket


class BaseProductAddBasketSerializer(serializers.Serializer):
    supplier = serializers.IntegerField(required=False)
    quantity = FormattedDecimalField(required=False)
    description = serializers.CharField(max_length=128, required=False, allow_null=True)
    force_new_line = serializers.BooleanField(required=False)


class ShopProductAddBasketSerializer(BaseProductAddBasketSerializer):
    shop_product = serializers.PrimaryKeyRelatedField(
        queryset=ShopProduct.objects.filter(purchasable=True),
        error_messages={"does_not_exist": _("Product does not exist.")}
    )
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
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.filter(status=ShopStatus.ENABLED))
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(deleted=False),
        error_messages={"does_not_exist": _("Product does not exist.")}
    )

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
    quantity = FormattedDecimalField()


class MethodIDSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)


class BasketCampaignCodeSerializer(serializers.Serializer):
    code = serializers.CharField()


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "reference_number"]


class BasketViewSet(PermissionHelperMixin, viewsets.GenericViewSet):
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

    queryset = Basket.objects.none()
    lookup_field = "uuid"
    serializer_class = BasketSerializer

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
            'source': getattr(self.request, "basket", None),
            'format': self.format_kwarg,
            'view': self
        }

    def get_serializer_class(self):
        if self.action == "abandoned":
            return StoredBasketSerializer
        return self.serializer_class

    def get_basket_shop(self):
        if settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
            shop_id = None
            uuid = self.kwargs.get(self.lookup_field, "")
            if uuid:
                shop_id = get_shop_id(self.kwargs.get(self.lookup_field, ""))

            if not shop_id:
                raise exceptions.ValidationError("No basket shop specified.")

            # this shop should be the shop associated with the basket
            return get_object_or_404(Shop, pk=shop_id)
        else:
            return Shop.objects.first()

    def process_request(self, with_basket=True, shop=None):
        """
        Add context to request that's expected by basket
        """
        request = self.request._request
        user = self.request.user
        request.shop = shop or self.get_basket_shop()
        request.person = get_person_contact(user)
        company = get_company_contact(user)
        request.customer = (company or request.person)
        if with_basket:
            request.basket = self.get_object()

    def retrieve(self, request, *args, **kwargs):
        """
        List the contents of the basket
        """
        self.process_request()
        return Response(self.get_serializer(request.basket).data)

    def _get_controlled_contacts_by_user(self, user):
        """
        List of contact ids the user controls

        The list includes the person contact linked to the user and all
        company contacts the user contact is linked to

        :param user: user object
        :type user: settings.USER_MODEL
        :return: list of contact ids the user controls
        :rtype: list(int)
        """
        contact = get_person_contact(user)
        if not contact:
            return []
        return [contact.pk] + list(contact.company_memberships.all().values_list("pk", flat=True))

    def get_object(self):
        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")
        shop = self.request.shop
        uuid = get_key(self.kwargs.get(self.lookup_field, ""))
        storage = get_storage()
        if not storage.basket_exists(uuid, shop):
            raise exceptions.NotFound()

        basket = basket_class(self.request._request, basket_name=uuid)
        try:
            basket._data = basket.storage.load(basket)
        except BasketCompatibilityError as error:
            raise exceptions.ValidationError(str(error))

        # ensure correct creator
        if not self.request.user.is_superuser:
            if not basket.shop == shop:
                raise exceptions.PermissionDenied("No permission")

            customer_id = (basket.customer.pk if basket.customer else None)
            controlled_contact_ids = self._get_controlled_contacts_by_user(self.request.user)
            is_staff = self.is_staff_user(shop, self.request.user)
            if customer_id and customer_id not in controlled_contact_ids and not is_staff:
                raise exceptions.PermissionDenied("No permission")

        return basket

    def is_staff_user(self, shop, user):
        return (shop and user.is_staff and shop.staff_members.filter(pk=user.pk).exists())

    def _handle_set_customer(self, request, basket, customer, orderer=None):
        try:
            cmd_kwargs = {
                "request": request,
                "basket": basket,
                "customer": customer or AnonymousContact(),
                "orderer": orderer
            }
            self._handle_cmd(self.request, "set_customer", cmd_kwargs)
        except ValidationError as exc:
            if exc.code in ["no_permission", "orderer_not_company_member", "not_company_member"]:
                raise exceptions.PermissionDenied(exc.message)
            else:
                raise exceptions.ValidationError(exc.message)

    @schema_serializer_class(NewBasketSerializer)
    @list_route(methods=['post'])
    def new(self, request, *args, **kwargs):
        """
        Create a brand new basket object
        """
        serializer = NewBasketSerializer(data=request.data)
        serializer.is_valid(True)
        data = serializer.validated_data

        self.process_request(with_basket=False, shop=data.get("shop"))
        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")
        basket = basket_class(request._request)

        if "customer" in data:
            customer = data["customer"]
        else:
            customer = get_company_contact(request.user) or get_person_contact(request.user)

        orderer = data.get("orderer", get_person_contact(request.user))

        # set the request basket to perform the basket command
        self.request.basket = basket
        self._handle_set_customer(
            request=self.request._request,
            basket=basket,
            customer=customer,
            orderer=orderer
        )

        stored_basket = basket.save()
        response_data = {
            "uuid": "%s-%s" % (request.shop.pk, stored_basket.key)
        }
        response_data.update(self.get_serializer(basket).data)
        return Response(data=response_data, status=status.HTTP_201_CREATED)

    def _handle_cmd(self, request, command, kwargs):
        cmd_dispatcher = get_basket_command_dispatcher(request)
        cmd_handler = cmd_dispatcher.get_command_handler(command)
        cmd_kwargs = cmd_dispatcher.preprocess_kwargs(command, kwargs)
        response = cmd_handler(**cmd_kwargs)
        return cmd_dispatcher.postprocess_response(command, cmd_kwargs, response)

    @schema_serializer_class(BasketRequestAbandonedSerializer)
    @list_route(methods=['get'])
    def abandoned(self, request, *args, **kwargs):
        if settings.SHUUP_BASKET_STORAGE_CLASS_SPEC != "shuup.core.basket.storage:DatabaseBasketStorage":
            raise exceptions.NotAcceptable("Invalid basket storage for this route.")

        serializer = BasketRequestAbandonedSerializer(data=request.query_params)
        serializer.is_valid(True)
        data = serializer.validated_data

        self.process_request(with_basket=False, shop=data["shop"])
        days = data.get("days_ago", 14)

        days_ago = None
        if days:
            days_ago = now() - datetime.timedelta(days=days)

        not_updated_in_hours = data.get("not_updated_in_hours", 2)
        late_cutoff = now() - datetime.timedelta(hours=not_updated_in_hours)

        if days_ago:
            updated_on_q = Q(updated_on__range=(days_ago, late_cutoff))
        else:
            updated_on_q = Q(updated_on__lte=late_cutoff)

        stored_baskets = Basket.objects.filter(
            shop=request.shop
        ).filter(updated_on_q, product_count__gte=0).exclude(
            deleted=True, finished=True, persistent=True
        )
        return Response(self.get_serializer(stored_baskets, many=True).data)

    @schema_serializer_class(ProductAddBasketSerializer)
    @detail_route(methods=['post'])
    def add(self, request, *args, **kwargs):
        """
        Adds a product to the basket
        """
        self.process_request()
        return self._add_product(request, *args, **kwargs)

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
                return Response(self.get_serializer(request.basket).data, status=status.HTTP_200_OK)
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
            return Response(self.get_serializer(request.basket).data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def update_quantity(self, request, *args, **kwargs):
        self.process_request()
        serializer = LineQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

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
            return Response(self.get_serializer(request.basket).data, status=status.HTTP_200_OK)

    @schema_serializer_class(BasketCampaignCodeSerializer)
    @detail_route(methods=['post'])
    def add_code(self, request, *args, **kwargs):
        """
        Add a campaign code to the basket
        """
        self.process_request()
        serializer = BasketCampaignCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cmd_kwargs = {
            "request": request._request,
            "basket": request.basket,
            "code": serializer.validated_data["code"]
        }
        response = self._handle_cmd(request, "add_campaign_code", cmd_kwargs)
        if response["ok"]:
            request.basket.save()
            return Response(self.get_serializer(request.basket).data, status=status.HTTP_200_OK)
        else:
            return Response({"code_invalid": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(BasketCampaignCodeSerializer)
    @detail_route(methods=['post'])
    def remove_code(self, request, *args, **kwargs):
        """
        Remove a campaign code from the basket
        """
        self.process_request()
        serializer = BasketCampaignCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cmd_kwargs = {
            "request": request._request,
            "basket": request.basket,
            "code": serializer.validated_data["code"]
        }
        response = self._handle_cmd(request, "remove_campaign_code", cmd_kwargs)
        if response["ok"]:
            request.basket.save()
            return Response(self.get_serializer(request.basket).data, status=status.HTTP_200_OK)
        else:
            return Response({"code_invalid": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def clear_codes(self, request, *args, **kwargs):
        """
        Remove all campaign codes from the basket
        """
        self.process_request()
        cmd_kwargs = {
            "request": request._request,
            "basket": request.basket
        }

        if len(request.basket.codes) == 0:
            return Response(self.get_serializer(request.basket).data, status=status.HTTP_200_OK)

        response = self._handle_cmd(request, "clear_campaign_codes", cmd_kwargs)
        if response["ok"]:
            request.basket.save()
            return Response(self.get_serializer(request.basket).data, status=status.HTTP_200_OK)
        else:
            return Response({"invalid_command": "Invalid command"}, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(BasketSetCustomerSerializer)
    @detail_route(methods=['post'])
    def set_customer(self, request, *args, **kwargs):
        """
        Set the basket customer
        """
        self.process_request()
        serializer = BasketSetCustomerSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self._handle_set_customer(
            request=request,
            basket=request.basket,
            customer=serializer.validated_data["customer"],
            orderer=serializer.validated_data.get("orderer", get_person_contact(request.user))
        )
        request.basket.refresh_lines()
        request.basket.save()
        return Response(self.get_serializer(request.basket).data, status=status.HTTP_200_OK)

    @schema_serializer_class(AddressSerializer)
    @detail_route(methods=['post'])
    def set_shipping_address(self, request, *args, **kwargs):
        return self._handle_setting_address(request, "shipping_address")

    @schema_serializer_class(AddressSerializer)
    @detail_route(methods=['post'])
    def set_billing_address(self, request, *args, **kwargs):
        return self._handle_setting_address(request, "billing_address")

    def _handle_setting_address(self, request, attr_field):
        """
        Set the address of the basket.
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

            setattr(request.basket, attr_field, address)
            request.basket.save()

        except ValidationError as exc:
            return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
        except MutableAddress.DoesNotExist:
            return Response({"error": "Address does not exist"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(self.get_serializer(request.basket).data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def set_shipping_method(self, request, *args, **kwargs):
        return self._handle_setting_method(request, ShippingMethod, "shipping_method")

    @detail_route(methods=['post'])
    def set_payment_method(self, request, *args, **kwargs):
        return self._handle_setting_method(request, PaymentMethod, "payment_method")

    def _handle_setting_method(self, request, model, attr_field):
        self.process_request()
        serializer = MethodIDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = None
        if request.data.get("id"):
            method = model.objects.get(id=request.data['id'])

        setattr(request.basket, attr_field, method)
        request.basket.save()

        return Response(self.get_serializer(request.basket).data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def create_order(self, request, *args, **kwargs):
        self.process_request()
        request.basket.status = OrderStatus.objects.get_default_initial()
        errors = []
        for error in request.basket.get_validation_errors():
            errors.append({"code": error.code, "message": "%s" % error.message})
        if len(errors):
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        order_creator = get_basket_order_creator()

        order = order_creator.create_order(request.basket)
        request.basket.finalize()
        return Response(data=OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'])
    def add_from_order(self, request, *args, **kwargs):
        """
        Add multiple products to the basket
        """
        self.process_request()
        errors = []
        order = self._get_order(request)

        if not order:
            return Response({"error": "invalid order"}, status=status.HTTP_404_NOT_FOUND)

        for line in order.lines.products():
            try:
                self._add_product(
                    request, add_data={"product": line.product_id, "shop": order.shop_id, "quantity": line.quantity}
                )
            except ValidationError as exc:
                errors.append({exc.code: exc.message})
            except ProductNotOrderableProblem as exc:
                errors.append({"error": "{}".format(exc)})
            except serializers.ValidationError as exc:
                errors.append({"error": str(exc)})
            except Exception as exc:
                errors.append({"error": str(exc)})
        if len(errors) > 0:
            return Response({"errors": errors}, status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(request.basket).data)

    def _get_order(self, request):
        order_queryset = Order.objects.filter(pk=request.data.get("order"))

        if self.request.basket.customer.id:
            order_queryset = order_queryset.filter(customer_id=request.basket.customer.id)
        else:
            order_queryset = order_queryset.filter(customer__isnull=True)

        if not self.request.shop.staff_members.filter(id=request.user.id).exists():
            # If the current user is not staff member the order customer needs to match
            # with the current user.
            order_queryset = order_queryset.filter(customer_id=get_person_contact(request.user).id)

        return order_queryset.first()

    def _add_product(self, request, *args, **kwargs):
        data = kwargs.pop("add_data", request.data)
        if "shop_product" in data:
            serializer = ShopProductAddBasketSerializer(data=data, context={"shop": request.shop})
        else:
            serializer = ProductAddBasketSerializer(data=data, context={"shop": request.shop})
        serializer.is_valid(True)
        cmd_kwargs = {
            "request": request._request,
            "basket": request._request.basket,
            "shop_id": serializer.data.get("shop") or serializer.validated_data["shop"].pk,
            "product_id": serializer.data.get("product") or serializer.validated_data["product"].pk,
            "quantity": serializer.validated_data.get("quantity", 1),
            "supplier_id": serializer.validated_data.get("supplier"),
            "force_new_line": serializer.validated_data.get("force_new_line", False)
        }
        # we call `add` directly, assuming the user will handle variations
        # as he can know all product variations easily through product API
        try:
            cmd_response = self._handle_cmd(request, "add", cmd_kwargs)
            request.basket.save()
            response_data = self.get_serializer(request.basket).data
            # return also the added line id
            response_data["add_line_id"] = cmd_response["line_id"]
            return Response(response_data)
        except ValidationError as exc:
            return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
        except ProductNotOrderableProblem as exc:
            return Response({"error": "{}".format(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @detail_route(methods=['get'])
    def taxes(self, request, *args, **kwargs):
        """
        Get taxes for basket
        """
        self.process_request()
        basket = request.basket
        tax_summary = basket.get_tax_summary()
        rows = [row.to_dict() for row in tax_summary]
        basket_summary_serializer = TaxSummarySerializer(data=rows, many=True)
        basket_summary_serializer.is_valid(True)
        lines = []
        for line in basket.get_final_lines(True):
            items = []
            for source_line_tax in line.taxes:
                source_line_tax.line_id = line.line_id
                items.append(source_line_tax)
            ts = SourceLineTaxSerializer(items, many=True)
            for row in ts.data:
                lines.append(row)
        return Response({
            "summary": basket_summary_serializer.validated_data,
            "lines": lines
        })
