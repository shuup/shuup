# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumField
from parler.models import TranslatableModel, TranslatedFields
from polymorphic.models import PolymorphicModel
from timezone_field.fields import TimeZoneField

from shoop.core.fields import InternalIdentifierField, LanguageField
from shoop.core.utils.name_mixin import NameMixin

from ._taxes import CustomerTaxGroup


@python_2_unicode_compatible
class ContactGroup(TranslatableModel):
    identifier = InternalIdentifierField(unique=True)
    members = models.ManyToManyField("Contact", related_name="groups", verbose_name=_('members'), blank=True)
    show_pricing = models.BooleanField(verbose_name=_('show as pricing option'), default=True)

    translations = TranslatedFields(
        name=models.CharField(max_length=64, verbose_name=_('name')),
    )

    class Meta:
        verbose_name = _('contact group')
        verbose_name_plural = _('contact groups')

    def __str__(self):
        return self.safe_translation_getter("name", default="Group<%s>" % (self.identifier or self.id))


@python_2_unicode_compatible
class Contact(NameMixin, PolymorphicModel):
    is_anonymous = False
    is_all_seeing = False
    default_tax_group_getter = None

    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('created on'))
    identifier = InternalIdentifierField(unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_('active'))
    # TODO: parent contact?
    default_shipping_address = models.ForeignKey(
        "MutableAddress", null=True, blank=True, related_name="+", verbose_name=_('shipping address'),
        on_delete=models.PROTECT
    )
    default_billing_address = models.ForeignKey(
        "MutableAddress", null=True, blank=True, related_name="+", verbose_name=_('billing address'),
        on_delete=models.PROTECT
    )
    default_shipping_method = models.ForeignKey(
        "ShippingMethod", verbose_name=_('default shipping method'), blank=True, null=True, on_delete=models.SET_NULL
    )
    default_payment_method = models.ForeignKey(
        "PaymentMethod", verbose_name=_('default payment method'), blank=True, null=True, on_delete=models.SET_NULL
    )

    language = LanguageField(verbose_name=_('language'), blank=True)
    marketing_permission = models.BooleanField(default=True, verbose_name=_('marketing permission'))
    phone = models.CharField(max_length=64, blank=True, verbose_name=_('phone'))
    www = models.URLField(max_length=128, blank=True, verbose_name=_('web address'))
    timezone = TimeZoneField(blank=True, null=True, verbose_name=_('time zone'))
    prefix = models.CharField(verbose_name=_('name prefix'), max_length=64, blank=True)
    name = models.CharField(max_length=256, verbose_name=_('name'))
    suffix = models.CharField(verbose_name=_('name suffix'), max_length=64, blank=True)
    name_ext = models.CharField(max_length=256, blank=True, verbose_name=_('name extension'))
    email = models.EmailField(max_length=256, blank=True, verbose_name=_('email'))

    tax_group = models.ForeignKey(
        "CustomerTaxGroup", blank=True, null=True, on_delete=models.PROTECT, verbose_name=_('tax group')
    )

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')

    def __init__(self, *args, **kwargs):
        if self.default_tax_group_getter:
            kwargs.setdefault("tax_group", self.default_tax_group_getter())
        super(Contact, self).__init__(*args, **kwargs)


class CompanyContact(Contact):
    default_tax_group_getter = CustomerTaxGroup.get_default_company_group

    members = models.ManyToManyField(
        "Contact", related_name="company_memberships", blank=True,
        verbose_name=_('members')
    )
    tax_number = models.CharField(
        max_length=32, blank=True,
        verbose_name=_("tax number"),
        help_text=_("e.g. EIN in US or VAT code in Europe"))

    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')


class Gender(Enum):
    UNDISCLOSED = "u"
    MALE = "m"
    FEMALE = "f"
    OTHER = "o"


class PersonContact(Contact):
    default_tax_group_getter = CustomerTaxGroup.get_default_person_group

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="contact",
        verbose_name=_('user')
    )
    gender = EnumField(Gender, default=Gender.UNDISCLOSED, max_length=4, verbose_name=_('gender'))
    birth_date = models.DateField(blank=True, null=True, verbose_name=_('birth date'))
    # TODO: Figure out how/when/if the name and email fields are updated from users

    class Meta:
        verbose_name = _('person')
        verbose_name_plural = _('persons')

    def save(self, *args, **kwargs):
        if self.user_id and not self.pk:  # Copy things
            user = self.user
            if not self.name:
                self.name = user.get_full_name()
            if not self.email:
                self.email = user.email
        return super(PersonContact, self).save(*args, **kwargs)

    @property
    def is_all_seeing(self):
        if self.user_id:
            return self.user.is_superuser


class AnonymousContact(Contact):
    pk = id = None
    is_anonymous = True

    class Meta:
        managed = False  # This isn't something that should actually exist in the database

    def __nonzero__(self):
        return False

    __bool__ = __nonzero__

    def __eq__(self, other):
        return type(self) == type(other)

    def save(self, *args, **kwargs):
        raise NotImplementedError("Not implemented: AnonymousContacts aren't saveable, silly")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Not implemented: AnonymousContacts don't exist in the database, silly")

    @property
    def groups(self):
        return ContactGroup.objects.none()


def get_person_contact(user):
    """
    Get PersonContact of given user.

    If given user is non-zero (evaluates true as bool) and not
    anonymous, return the PersonContact of the user.  If there is no
    PersonContact for the user yet, create it first.  When this creation
    happens, details (name, email, is_active) are copied from the user.

    If given user is None (or otherwise evaluates as false) or
    anonymous, return the AnonymousContact.

    :param user: User object (or None) to get contact for
    :type user: django.contrib.auth.models.User|None
    :return: PersonContact of the user or AnonymousContact
    :rtype: PersonContact|AnonymousContact
    """
    if not user or user.is_anonymous():
        return AnonymousContact()
    defaults = {
        'is_active': user.is_active,
        'name': user.get_full_name(),
        'email': user.email,
    }
    return PersonContact.objects.get_or_create(user=user, defaults=defaults)[0]
