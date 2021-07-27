# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.utils.crypto import get_random_string

from shuup.core.models import CompanyContact, Contact, Order, PersonContact, Shop
from shuup.core.models._addresses import Address
from shuup.core.utils.product_subscription import UserModel
from shuup.gdpr.signals import anonymization_requested


class Anonymizer(object):
    mapping = {
        "phone": "_null_phone",
        "ip_address": "_null_ip",
        "first_name": "_null_name",
        "last_name": "_null_name",
        "name": "_null_name",
        "postal_code": "_null_zip",
        "zip_code": "_null_zip",
        "www": "_blank_value",
        "prefix": "_blank_value",
        "suffix": "_blank_value",
        "name_ext": "_blank_value",
        "merchant_notes": "_blank_value",
        "street": "_random_string",
        "street1": "_random_string",
        "street2": "_random_string",
        "street3": "_random_string",
        "street_address": "_random_string",
        "tax_number": "_random_number",
        "city": "_random_string",
        "longitude": "_none_value",
        "latitude": "_none_value",
        "birth_date": "_none_value",
        "data": "_none_value",
        "email": "_null_email",
        "username": "_random_username",
    }

    def _random_string(self, len=8):
        return get_random_string(len)

    def _none_value(self):
        return None

    def _blank_value(self):
        return ""

    def _null_zip(self):
        return get_random_string(6)

    def _null_ip(self):
        return "0.0.0.0"

    def _null_email(self):
        return "%s@%s.com" % (get_random_string(10), get_random_string(8))

    def _null_name(self):
        return get_random_string(8)

    def _null_phone(self):
        return get_random_string(9, "1234567890")

    def _random_number(self):
        return int(get_random_string(9, "123456789"))

    def _random_username(self):
        return get_random_string(20, "1234567890")

    def _anonymize_contact(self, pk):
        contact = Contact.objects.get(pk=pk)

        # make sure to remove from marketing before we lost the contact email
        contact.marketing_permission = False
        contact.save()

        # anonymize all saved addresses
        for saved_address in contact.savedaddress_set.all():
            self._anonymize_object(saved_address.address)

        # anonymize all orders
        for order in contact.customer_orders.all():
            self._anonymize_order(order)

        # anonymize all Front baskets
        for basket in contact.customer_baskets.all():
            self._anonymize_object(basket)

        # anonymize all Core baskets
        for basket in contact.customer_core_baskets.all():
            self._anonymize_object(basket)

        self._anonymize_object(contact.default_shipping_address)
        self._anonymize_object(contact.default_billing_address)
        self._anonymize_object(contact)

        for order in Order.objects.incomplete().filter(customer=contact):
            order.set_canceled()

        contact.is_active = False
        contact.save()

    def _anonymize_company(self, company):
        if not company:
            return
        assert isinstance(company, CompanyContact)
        self._anonymize_contact(company.id)

    def _anonymize_person(self, person):
        if not person:
            return
        assert isinstance(person, PersonContact)

        for order in person.orderer_orders.all():
            self._anonymize_order(order)

        for basket in person.orderer_baskets.all():
            self._anonymize_object(basket)

        for basket in person.orderer_core_baskets.all():
            self._anonymize_object(basket)

        # anonymize related user
        if hasattr(person, "user") and person.user:
            self._anonymize_user(person.user)

        # check if there is any company related to the person
        # if so, anonymize it if he is the unique member
        for company in person.company_memberships.all():
            if company.members.count() == 1:
                self._anonymize_company(company)

        self._anonymize_contact(person.pk)

    def _anonymize_order(self, order):
        assert isinstance(order, Order)
        self._anonymize_object(order)

        if order.shipping_address:
            self._anonymize_object(order.shipping_address, save=False)
            Address.save(order.shipping_address)  # bypass Protected model save() invoking super directly

        if order.billing_address:
            self._anonymize_object(order.billing_address, save=False)
            Address.save(order.billing_address)

    def _anonymize_object(self, obj, save=True):
        if not obj:
            return

        for field, attr in six.iteritems(self.mapping):
            if not hasattr(obj, field):
                continue
            val = getattr(self, attr)()

            try:
                setattr(obj, field, val)
            except AttributeError:
                pass

        if save:
            obj.save()

    def _anonymize_queryset(self, qs):
        for qs_obj in qs:
            self._anonymize_object(qs_obj)

    def _anonymize_user(self, user):
        if not user:
            return
        self._anonymize_object(user)
        user.is_active = False
        user.save()

    def anonymize(self, shop: Shop, contact: Contact = None, user: UserModel = None):
        if isinstance(contact, PersonContact):
            self._anonymize_person(contact)
        elif isinstance(contact, CompanyContact):
            self._anonymize_company(contact)

        if user:
            self._anonymize_user(user)

        anonymization_requested.send(type(self), shop=shop, contact=contact, user=user)
