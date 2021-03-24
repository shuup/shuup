# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from enumfields import Enum, EnumIntegerField

from shuup.core.utils.name_mixin import NameMixin
from shuup.utils.analog import define_log_model
from shuup.utils.importing import cached_load
from shuup.utils.models import get_data_dict

from ._base import ChangeProtected, ShuupModel

REGION_ISO3166 = {
    "europe": set(
        (
            "AD",
            "AL",
            "AM",
            "AT",
            "AX",
            "AZ",
            "BA",
            "BE",
            "BG",
            "BY",
            "CH",
            "CY",
            "CZ",
            "DE",
            "DK",
            "EE",
            "ES",
            "FI",
            "FO",
            "FR",
            "GB",
            "GE",
            "GG",
            "GI",
            "GR",
            "HR",
            "HU",
            "IE",
            "IM",
            "IS",
            "IT",
            "JE",
            "KZ",
            "LI",
            "LT",
            "LU",
            "LV",
            "MC",
            "MD",
            "ME",
            "MK",
            "MT",
            "NL",
            "NO",
            "PL",
            "PT",
            "RO",
            "RS",
            "RU",
            "SE",
            "SI",
            "SJ",
            "SK",
            "SM",
            "TR",
            "UA",
            "VA",
        )
    ),
    "european-union": set(
        (
            "AT",
            "BE",
            "BG",
            "CY",
            "CZ",
            "DE",
            "DK",
            "EE",
            "ES",
            "FI",
            "FR",
            "GR",
            "HR",
            "HU",
            "IE",
            "IT",
            "LT",
            "LU",
            "LV",
            "MT",
            "NL",
            "PL",
            "PT",
            "RO",
            "SE",
            "SI",
            "SK",
        )
    ),
}


class SavedAddressRole(Enum):
    SHIPPING = 1
    BILLING = 2

    class Labels:
        SHIPPING = _("shipping address")
        BILLING = _("billing address")


class SavedAddressStatus(Enum):
    DISABLED = 0
    ENABLED = 1

    class Labels:
        DISABLED = _("disabled")
        ENABLED = _("enabled")


class Address(NameMixin, ShuupModel):
    """
    Abstract base class of addresses.
    """

    prefix = models.CharField(
        verbose_name=_("name prefix"),
        max_length=64,
        blank=True,
        help_text=_("The name prefix. For example, Mr, Mrs, Ms, Dr, etc."),
    )
    name = models.CharField(verbose_name=_("name"), max_length=255, help_text=_("The name for the address."))
    suffix = models.CharField(
        verbose_name=_("name suffix"),
        max_length=64,
        blank=True,
        help_text=_("The name suffix. For example, Jr, Sr, etc."),
    )
    name_ext = models.CharField(
        verbose_name=_("name extension"),
        max_length=255,
        blank=True,
        help_text=_(
            "Any other text to display along with the address. "
            "This could be department names (for companies) or titles (for people)."
        ),
    )
    company_name = models.CharField(
        verbose_name=_("company name"), max_length=255, blank=True, help_text=_("The company name for the address.")
    )
    tax_number = models.CharField(
        verbose_name=_("tax number"),
        max_length=64,
        blank=True,
        help_text=_("The business tax number. For example, EIN in the USA or VAT code in the EU."),
    )
    phone = models.CharField(
        verbose_name=_("phone"), max_length=64, blank=True, help_text=_("The primary phone number for the address.")
    )
    email = models.EmailField(
        verbose_name=_("email"), max_length=128, blank=True, help_text=_("The primary email for the address.")
    )
    street = models.CharField(verbose_name=_("street"), max_length=255, help_text=_("The street address."))
    street2 = models.CharField(
        verbose_name=_("street (2)"), max_length=255, blank=True, help_text=_("An additional street address line.")
    )
    street3 = models.CharField(
        verbose_name=_("street (3)"), max_length=255, blank=True, help_text=_("Any additional street address line.")
    )
    postal_code = models.CharField(
        verbose_name=_("postal code"), max_length=64, blank=True, help_text=_("The address postal/zip code.")
    )
    city = models.CharField(verbose_name=_("city"), max_length=255, help_text=_("The address city."))
    region_code = models.CharField(
        verbose_name=_("region code"), max_length=64, blank=True, help_text=_("The address region, province, or state.")
    )
    region = models.CharField(
        verbose_name=_("region"), max_length=64, blank=True, help_text=_("The address region, province, or state.")
    )
    country = CountryField(verbose_name=_("country"), help_text=_("The address country."))
    longitude = models.DecimalField(null=True, blank=True, max_digits=9, decimal_places=6)
    latitude = models.DecimalField(null=True, blank=True, max_digits=9, decimal_places=6)

    class Meta:
        abstract = True
        verbose_name = _("address")
        verbose_name_plural = _("addresses")

    # Properties
    @property
    def is_home(self):
        if not settings.SHUUP_ADDRESS_HOME_COUNTRY:
            return False
        return self.country.code == settings.SHUUP_ADDRESS_HOME_COUNTRY.upper()

    @property
    def is_european_union(self):
        return self.country in REGION_ISO3166["european-union"]

    def __str__(self):
        return " / ".join(self.as_string_list())

    def as_string_list(self, locale=None):
        formatter = cached_load("SHUUP_ADDRESS_FORMATTER_SPEC")
        return formatter().address_as_string_list(self, locale)

    def __iter__(self):
        return iter(self.as_string_list())

    def to_immutable(self):
        """
        Get or create saved ImmutableAddress from self.

        :rtype: ImmutableAddress
        :return: Saved ImmutableAddress with same data as self.
        """
        data = get_data_dict(self)
        return ImmutableAddress.from_data(data)

    def to_mutable(self):
        """
        Get a new MutableAddress from self.

        :rtype: MutableAddress
        :return: Fresh unsaved MutableAddress with same data as self.
        """
        data = get_data_dict(self)
        return MutableAddress.from_data(data)


class MutableAddress(Address):
    """
    An address that can be changed.

    Mutable addresses are used for e.g. contact's saved addresses.
    They are saved as new immutable addresses when used in e.g. orders.

    Mutable addresses can be created with `MutableAddress.from_data`
    or with the `to_mutable` method of `Address` objects.
    """

    @classmethod
    def from_data(cls, data):
        """
        Construct mutable address from a data dictionary.

        :param data: data for address
        :type data: dict[str,str]
        :return: Unsaved mutable address
        :rtype: MutableAddress
        """
        return cls(**data)


class ImmutableAddress(ChangeProtected, Address):
    """
    An address that can not be changed.

    Immutable addresses are used for orders, etc., where subsequent
    edits to the original address (for example an user's default address)
    must not affect past business data.

    Immutable addresses can be created directly, with the `.from_data()`
    method, or by creating an immutable copy of an existing `MutableAddress`
    with the `Address.to_immutable()` method.
    """

    @classmethod
    def from_data(cls, data):
        """
        Get or create immutable address with given data.

        :param data: data for address
        :type data: dict[str,str]
        :return: Saved immutable address
        :rtype: ImmutableAddress
        """
        # Populate all known address fields even if not originally in `data`
        data_with_all_fields = get_data_dict(cls(**data))
        address = cls.objects.filter(**data_with_all_fields).first()
        return address if address else cls.objects.create(**data_with_all_fields)

    def to_immutable(self):
        if self.pk:
            return self
        return super(ImmutableAddress, self).to_immutable()


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


class SavedAddress(ShuupModel):
    """
    Model for saving multiple addresses in an 'address book' of sorts.
    """

    owner = models.ForeignKey(on_delete=models.CASCADE, to="Contact", verbose_name=_("owner"))
    address = models.ForeignKey(
        on_delete=models.CASCADE, to=MutableAddress, verbose_name=_("address"), related_name="saved_addresses"
    )
    role = EnumIntegerField(SavedAddressRole, verbose_name=_("role"), default=SavedAddressRole.SHIPPING)
    status = EnumIntegerField(SavedAddressStatus, default=SavedAddressStatus.ENABLED, verbose_name=_("status"))
    title = models.CharField(max_length=255, blank=True, verbose_name=_("title"))
    objects = SavedAddressManager()

    class Meta:
        verbose_name = _("saved address")
        verbose_name_plural = _("saved addresses")
        ordering = ("owner_id", "role", "title")

    def __str__(self):
        return "%s" % self.get_title()

    def get_title(self):
        """
        Returns the display title for this `SavedAddress` instance. Defaults
        to a short representation of the address.

        This method should be used instead of accessing the `title` field
        directly when displaying `SavedAddress` objects.
        """
        return self.title.strip() if self.title else six.text_type(self.address)


SavedAddressLogEntry = define_log_model(SavedAddress)
