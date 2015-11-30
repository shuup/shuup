# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.conf import settings
from django.db import models
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from enumfields import Enum, EnumIntegerField

from shoop.core.excs import ImmutabilityError
from shoop.core.utils.name_mixin import NameMixin
from shoop.utils.i18n import get_current_babel_locale
from shoop.utils.models import copy_model_instance, get_data_dict

REGION_ISO3166 = {
    "europe": set((
        "AD", "AL", "AM", "AT", "AX", "AZ", "BA", "BE", "BG", "BY", "CH", "CY", "CZ",
        "DE", "DK", "EE", "ES", "FI", "FO", "FR", "GB", "GE", "GG", "GI", "GR", "HR",
        "HU", "IE", "IM", "IS", "IT", "JE", "KZ", "LI", "LT", "LU", "LV", "MC", "MD",
        "ME", "MK", "MT", "NL", "NO", "PL", "PT", "RO", "RS", "RU", "SE", "SI", "SJ",
        "SK", "SM", "TR", "UA", "VA"
    )),
    "european-union": set((
        "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GB", "GR",
        "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI",
        "SK"
    ))
}


class SavedAddressRole(Enum):
    SHIPPING = 1
    BILLING = 2

    class Labels:
        SHIPPING = _('shipping address')
        BILLING = _('billing address')


class SavedAddressStatus(Enum):
    DISABLED = 0
    ENABLED = 1

    class Labels:
        DISABLED = _('disabled')
        ENABLED = _('enabled')


class AddressManager(models.Manager):
    def try_get_exactly_like(self, object, ignore_fields=()):
        """
        Try to find an immutable Address that is data-wise exactly like the given object.

        :param object: A model -- probably an Address
        :type object: Address|models.Model
        :param ignore_fields: Iterable of field names to ignore while comparing.
        :type ignore_fields: Iterable[str]

        :return: Address|None
        """
        data = get_data_dict(object)
        for field_name in ignore_fields:
            data.pop(field_name, None)
        data["is_immutable"] = True
        return self.get_queryset().filter(**data).first()

    def from_address_form(self, address_form, company=None):
        """
        Get an address from an AddressForm (or similar-enough ModelForm).

        May return an existing immutable address, or a new, unsaved address.

        :param address_form: Address form.
        :type address_form: django.forms.ModelForm
        :param company: Optional CompanyContact object.
                        If passed, the company information will be injected into the address.
        :type company: shoop.shop.models.contacts.CompanyContact

        :return: Address
        """

        address = address_form.save(commit=False)

        if company:
            address.company = company.name
            address.tax_number = company.tax_number

        return (self.try_get_exactly_like(address) or address)


@python_2_unicode_compatible
class Address(NameMixin, models.Model):
    objects = AddressManager()
    prefix = models.CharField(verbose_name=_('name prefix'), max_length=64, blank=True)
    name = models.CharField(verbose_name=_('name'), max_length=255)
    suffix = models.CharField(verbose_name=_('name suffix'), max_length=64, blank=True)
    name_ext = models.CharField(verbose_name=_('name extension'), max_length=255, blank=True)
    company_name = models.CharField(verbose_name=_('company name'), max_length=255, blank=True)
    tax_number = models.CharField(verbose_name=_('Tax number'), max_length=64, blank=True)
    phone = models.CharField(verbose_name=_('phone'), max_length=64, blank=True)
    email = models.EmailField(verbose_name=_('email'), max_length=128, blank=True)
    street = models.CharField(verbose_name=_('street'), max_length=255)
    street2 = models.CharField(verbose_name=_('street (2)'), max_length=255, blank=True)
    street3 = models.CharField(verbose_name=_('street (3)'), max_length=255, blank=True)
    postal_code = models.CharField(verbose_name=_('ZIP / Postal code'), max_length=64, blank=True)
    city = models.CharField(verbose_name=_('city'), max_length=255)
    region_code = models.CharField(verbose_name=_('region code'), max_length=16, blank=True)
    region = models.CharField(verbose_name=_('region'), max_length=64, blank=True)
    country = CountryField(verbose_name=_('country'))
    is_immutable = models.BooleanField(default=False, db_index=True, editable=False, verbose_name=_('immutable'))

    # Properties
    @property
    def is_home(self):
        if not settings.SHOOP_ADDRESS_HOME_COUNTRY:
            return False
        return self.country.code == settings.SHOOP_ADDRESS_HOME_COUNTRY.upper()

    @property
    def is_european_union(self):
        return (self.country in REGION_ISO3166["european-union"])

    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')

    def __str__(self):
        return " / ".join(self.as_string_list())

    def save(self, *args, **kwargs):
        if self.is_immutable and not kwargs.pop("__setting_immutability", None) and self.pk:
            raise ImmutabilityError(
                "This %r object is immutable. Use .copy() to get a pristine instance." % self.__class__
            )
        return super(Address, self).save(*args, **kwargs)

    def copy(self):
        copy = copy_model_instance(self)
        copy.is_immutable = False
        return copy

    def set_immutable(self):
        self.is_immutable = True
        return self.save(__setting_immutability=True)

    def as_string_list(self, locale=None):
        locale = locale or get_current_babel_locale()
        country = self.country.code.upper()

        base_lines = [
            self.company_name,
            self.full_name,
            self.name_ext,
            self.street,
            self.street2,
            self.street3,
            "%s %s %s" % (self.region_code, self.postal_code, self.city),
            self.region,
            locale.territories.get(country, country) if not self.is_home else None
        ]

        stripped_lines = [force_text(line).strip() for line in base_lines if line]
        return [s for s in stripped_lines if (s and len(s) > 1)]

    def __iter__(self):
        return iter(self.as_string_list())


class SavedAddressManager(models.Manager):
    """
    Custom manager for `SavedAddress` objects.
    """

    def for_owner(self, owner):
        """
        Returns a `QuerySet` containing `SavedAddress` objects whose owner
        is the given `owner`.
        """
        if owner:
            return self.get_queryset().filter(owner=owner)
        return self.none()


@python_2_unicode_compatible
class SavedAddress(models.Model):
    """
    Model for saving multiple addresses in an 'address book' of sorts.
    """
    owner = models.ForeignKey("Contact", on_delete=models.CASCADE)
    address = models.ForeignKey(
        Address, verbose_name=_('address'), related_name="saved_addresses", on_delete=models.CASCADE)
    role = EnumIntegerField(SavedAddressRole, verbose_name=_('role'), default=SavedAddressRole.SHIPPING)
    status = EnumIntegerField(SavedAddressStatus, default=SavedAddressStatus.ENABLED, verbose_name=_('status'))
    title = models.CharField(max_length=255, blank=True, verbose_name=_('title'))
    objects = SavedAddressManager()

    class Meta:
        verbose_name = _('saved address')
        verbose_name_plural = _('saved addresses')
        ordering = ("owner_id", "role", "title")

    def __str__(self):
        return u"%s" % self.get_title()

    def get_title(self):
        """
        Returns the display title for this `SavedAddress` instance. Defaults
        to a short representation of the address.

        This method should be used instead of accessing the `title` field
        directly when displaying `SavedAddress` objects.
        """
        return self.title.strip() if self.title else six.text_type(self.address)
