# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.contrib.auth import get_user_model
from rest_framework import serializers

from shuup.api.fields import EnumField
from shuup.core.models import (
    Basket, CompanyContact, CompanyContactLogEntry, Contact,
    ContactGroupLogEntry, Gender, MutableAddress, Order, OrderLine,
    OrderLineType, PaymentStatus, PersonContact, PersonContactLogEntry,
    SavedAddress, SavedAddressRole, SavedAddressStatus, ShippingStatus
)
from shuup.front.models import StoredBasket
from shuup.gdpr.models import GDPRCookieCategory, GDPRUserConsent
from shuup.utils.analog import LogEntryKind


class ContactLogEntrySerializer(serializers.ModelSerializer):
    kind = EnumField(LogEntryKind)

    class Meta:
        model = ContactGroupLogEntry
        exclude = ()


class CompanyContactLogEntrySerializer(ContactLogEntrySerializer):
    class Meta:
        model = CompanyContactLogEntry
        exclude = ()


class PersonContactLogEntrySerializer(ContactLogEntrySerializer):
    class Meta:
        model = PersonContactLogEntry
        exclude = ()


class GDPRConsentDocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(source="page.title")
    modified_on = serializers.DateTimeField(source="page.modified_on")


class GDPRConsentCookieCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GDPRCookieCategory
        exclude = ()


class GDPRConsentSerializer(serializers.ModelSerializer):
    documents = GDPRConsentDocumentSerializer(many=True)

    class Meta:
        model = GDPRUserConsent
        exclude = ()


class UserSerializer(serializers.ModelSerializer):
    gdpr_consents = GDPRConsentSerializer(many=True)

    class Meta:
        model = get_user_model()
        exclude = ("password",)     # TODO: should we also return this?


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutableAddress
        exclude = ()


class OrderLineSerializer(serializers.ModelSerializer):
    type = EnumField(OrderLineType)

    class Meta:
        model = OrderLine
        exclude = ()


class OrderSerializer(serializers.ModelSerializer):
    payment_status = EnumField(PaymentStatus)
    shipping_status = EnumField(ShippingStatus)
    billing_address = AddressSerializer()
    shipping_address = AddressSerializer()
    lines = OrderLineSerializer(many=True)

    class Meta:
        model = Order
        exclude = ()


class SavedAddressSerializer(serializers.ModelSerializer):
    role = EnumField(SavedAddressRole)
    status = EnumField(SavedAddressStatus)
    address = AddressSerializer()

    class Meta:
        model = SavedAddress
        exclude = ()


class CoreBasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basket
        exclude = ()


class FrontSavedBasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoredBasket
        exclude = ()


class ContactSerializer(serializers.ModelSerializer):
    default_billing_address = AddressSerializer()
    default_shipping_address = AddressSerializer()
    saved_addresses = SavedAddressSerializer(many=True, source="savedaddress_set")
    orders = OrderSerializer(many=True, source="customer_orders")
    log_entries = ContactLogEntrySerializer(many=True)
    saved_baskets = FrontSavedBasketSerializer(many=True, source="customer_baskets")
    baskets = CoreBasketSerializer(many=True, source="customer_core_baskets")

    class Meta:
        model = Contact
        exclude = ("polymorphic_ctype",)


class GDPRCompanyContactSerializer(serializers.ModelSerializer):
    log_entries = PersonContactLogEntrySerializer(many=True)

    class Meta:
        model = CompanyContact
        fields = "__all__"


class GDPRPersonContactSerializer(ContactSerializer):
    gender = EnumField(Gender)
    user = UserSerializer()
    log_entries = PersonContactLogEntrySerializer(many=True)
    company_memberships = GDPRCompanyContactSerializer(many=True)

    class Meta:
        model = PersonContact
        exclude = ("polymorphic_ctype",)
