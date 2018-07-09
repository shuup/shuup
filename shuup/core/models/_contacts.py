# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatedFields
from timezone_field.fields import TimeZoneField

from shuup import configuration
from shuup.core.fields import InternalIdentifierField, LanguageField
from shuup.core.pricing import PriceDisplayOptions
from shuup.core.utils.users import (
    is_user_all_seeing, should_force_anonymous_contact,
    should_force_person_contact
)
from shuup.utils.analog import define_log_model

from ._base import PolymorphicShuupModel, TranslatableShuupModel
from ._taxes import CustomerTaxGroup

DEFAULT_COMPANY_GROUP_IDENTIFIER = "default_company_group"
DEFAULT_PERSON_GROUP_IDENTIFIER = "default_person_group"
DEFAULT_ANONYMOUS_GROUP_IDENTIFIER = "default_anonymous_group"

PROTECTED_CONTACT_GROUP_IDENTIFIERS = [
    DEFAULT_COMPANY_GROUP_IDENTIFIER,
    DEFAULT_PERSON_GROUP_IDENTIFIER,
    DEFAULT_ANONYMOUS_GROUP_IDENTIFIER
]


class ContactGroupQuerySet(TranslatableQuerySet):
    def with_price_display_options(self):
        return self.filter(
            models.Q(show_prices_including_taxes__isnull=False) |
            models.Q(hide_prices__isnull=False))

    def all_except_defaults(self):
        return self.exclude(identifier__in=PROTECTED_CONTACT_GROUP_IDENTIFIERS)


class ContactGroup(TranslatableShuupModel):
    identifier = InternalIdentifierField(unique=True)
    members = models.ManyToManyField("Contact", related_name="groups", verbose_name=_('members'), blank=True)
    show_pricing = models.BooleanField(verbose_name=_('show as pricing option'), default=True)
    show_prices_including_taxes = models.NullBooleanField(
        default=None, null=True, blank=True,
        verbose_name=_("show prices including taxes"))
    hide_prices = models.NullBooleanField(
        default=None, null=True, blank=True,
        verbose_name=_("hide prices"))

    translations = TranslatedFields(
        name=models.CharField(max_length=64, verbose_name=_('name'), help_text=_(
            "The contact group name. "
            "Contact groups can be used to target sales and campaigns to specific set of users."
        )),
    )

    objects = ContactGroupQuerySet.as_manager()

    class Meta:
        verbose_name = _('contact group')
        verbose_name_plural = _('contact groups')

    def get_price_display_options(self):
        return PriceDisplayOptions(
            include_taxes=self.show_prices_including_taxes,
            show_prices=(not self.hide_prices),
        )

    def can_delete(self):
        return bool(
            self.pk and
            self.identifier not in PROTECTED_CONTACT_GROUP_IDENTIFIERS and
            not self.customer_group_orders.count()
        )

    def delete(self, *args, **kwargs):
        if not self.can_delete():
            raise models.ProtectedError(_("Can't delete. This object is protected."), [self])
        super(ContactGroup, self).delete(*args, **kwargs)


@python_2_unicode_compatible
class Contact(PolymorphicShuupModel):
    is_anonymous = False
    is_all_seeing = False
    default_tax_group_getter = None
    default_contact_group_identifier = None
    default_contact_group_name = None

    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('created on'))
    modified_on = models.DateTimeField(
        auto_now=True, editable=False, db_index=True, null=True, verbose_name=_('modified on'))
    identifier = InternalIdentifierField(unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_('active'), help_text=_(
        "Check this if the contact is an active customer."
    ))
    shops = models.ManyToManyField("shuup.Shop", blank=True, verbose_name=_('shops'), help_text=_(
        "Inform which shops have access to this contact."
    ))
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

    _language = LanguageField(verbose_name=_('language'), blank=True, help_text=_(
        "The primary language to be used in all communications with the contact."
    ))
    marketing_permission = models.BooleanField(default=False, verbose_name=_('marketing permission'), help_text=_(
        "Check this if the contact can receive marketing and promotional materials."
    ))
    phone = models.CharField(max_length=64, blank=True, verbose_name=_('phone'), help_text=_(
        "The primary phone number of the contact."
    ))
    www = models.URLField(max_length=128, blank=True, verbose_name=_('web address'), help_text=_(
        "The web address of the contact, if any."
    ))
    timezone = TimeZoneField(blank=True, null=True, verbose_name=_('time zone'), help_text=_(
        "The timezone in which the contact resides. This can be used to target the delivery of promotional materials "
        "at a particular time."
    ))
    prefix = models.CharField(verbose_name=_('name prefix'), max_length=64, blank=True, help_text=_(
        "The name prefix of the contact. For example, Mr, Mrs, Dr, etc."
    ))
    name = models.CharField(max_length=256, verbose_name=_('name'), help_text=_("The contact name"))
    suffix = models.CharField(verbose_name=_('name suffix'), max_length=64, blank=True, help_text=_(
        "The name suffix of the contact. For example, Sr, Jr, etc."
    ))
    name_ext = models.CharField(max_length=256, blank=True, verbose_name=_('name extension'))
    email = models.EmailField(max_length=256, blank=True, verbose_name=_('email'), help_text=_(
        "The email that will receive order confirmations and promotional materials (if permitted)."
    ))

    tax_group = models.ForeignKey(
        "CustomerTaxGroup", blank=True, null=True, on_delete=models.PROTECT, verbose_name=_('tax group'),
        help_text=_(
            "Select the contact tax group to use for this contact. "
            "Tax groups can be used to customize the tax rules the that apply to any of this contacts orders. "
            "Tax groups are defined in Settings - Customer Tax Groups and can be applied to tax rules in "
            "Settings - Tax Rules"
        )
    )
    merchant_notes = models.TextField(blank=True, verbose_name=_('merchant notes'), help_text=_(
        "Enter any private notes for this customer that are only accessible in Shuup admin."
    ))
    account_manager = models.ForeignKey("PersonContact", blank=True, null=True, verbose_name=_('account manager'))

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')

    def __init__(self, *args, **kwargs):
        if self.default_tax_group_getter:
            kwargs.setdefault("tax_group", self.default_tax_group_getter())
        super(Contact, self).__init__(*args, **kwargs)

    @property
    def full_name(self):
        return (" ".join([self.prefix, self.name, self.suffix])).strip()

    @property
    def language(self):
        if self._language is not None:
            return self._language
        return configuration.get(None, "default_contact_language", settings.LANGUAGE_CODE)

    @language.setter
    def language(self, value):
        self._language = value

    def get_price_display_options(self):
        """
        Get price display options of the contact.

        If the default group (`get_default_group`) defines price display
        options and the contact is member of it, return it.

        If contact is not (anymore) member of the default group or the
        default group does not define options, return one of the groups
        which defines options.  If there is more than one such groups,
        it is undefined which options will be used.

        If contact is not a member of any group that defines price
        display options, return default constructed
        `PriceDisplayOptions`.

        Subclasses may still override this default behavior.

        :rtype: PriceDisplayOptions
        """
        groups_with_options = self.groups.with_price_display_options()
        if groups_with_options:
            default_group = self.get_default_group()
            if groups_with_options.filter(pk=default_group.pk).exists():
                group_with_options = default_group
            else:
                # Contact was removed from the default group.
                group_with_options = groups_with_options.first()
            return group_with_options.get_price_display_options()
        return PriceDisplayOptions()

    def save(self, *args, **kwargs):
        add_to_default_group = bool(self.pk is None and self.default_contact_group_identifier)
        super(Contact, self).save(*args, **kwargs)
        if add_to_default_group:
            self.groups.add(self.get_default_group())

    @classmethod
    def get_default_group(cls):
        """
        Get or create default contact group for the class.

        Identifier of the group is specified by the class property
        `default_contact_group_identifier`.

        If new group is created, its name is set to value of
        `default_contact_group_name` class property.

        :rtype: core.models.ContactGroup
        """
        obj, created = ContactGroup.objects.get_or_create(
            identifier=cls.default_contact_group_identifier,
            defaults={
                "name": cls.default_contact_group_name
            }
        )
        return obj


class CompanyContact(Contact):
    default_tax_group_getter = CustomerTaxGroup.get_default_company_group
    default_contact_group_identifier = DEFAULT_COMPANY_GROUP_IDENTIFIER
    default_contact_group_name = _("Company Contacts")

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

    @property
    def full_name(self):
        return self.name + (" / %s" % self.name_ext if self.name_ext else "")


class Gender(Enum):
    UNDISCLOSED = "u"
    MALE = "m"
    FEMALE = "f"
    OTHER = "o"

    class Labels:
        UNDISCLOSED = _('undisclosed')
        MALE = _('male')
        FEMALE = _('female')
        OTHER = _('other')


class PersonContact(Contact):
    default_tax_group_getter = CustomerTaxGroup.get_default_person_group
    default_contact_group_identifier = DEFAULT_PERSON_GROUP_IDENTIFIER
    default_contact_group_name = _("Person Contacts")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="contact",
        verbose_name=_('user')
    )
    gender = EnumField(Gender, default=Gender.UNDISCLOSED, max_length=4, verbose_name=_('gender'), help_text=_(
        "The gender of the contact."
    ))
    birth_date = models.DateField(blank=True, null=True, verbose_name=_('birth date'), help_text=_(
        "The birth date of the contact."
    ))
    first_name = models.CharField(max_length=120, blank=True, verbose_name=_('first name'), help_text=_(
        "The first name of the contact."
    ))
    last_name = models.CharField(max_length=120, blank=True, verbose_name=_('last name'), help_text=_(
        "The last name of the contact."
    ))
    # TODO: Figure out how/when/if the name and email fields are updated from users

    class Meta:
        verbose_name = _('person')
        verbose_name_plural = _('persons')

    def __init__(self, *args, **kwargs):
        name = kwargs.get('name')
        if name:
            (first_name, last_name) = _split_name(name)
            kwargs['first_name'] = first_name
            kwargs['last_name'] = last_name
        super(PersonContact, self).__init__(*args, **kwargs)

    @property
    def name(self):
        names = (self.first_name, self.last_name)
        return " ".join(x for x in names if x)

    @name.setter
    def name(self, value):
        (self.first_name, self.last_name) = _split_name(value)

    def get_deferred_fields(self):
        # Workaround
        # Refs:
        #   https://code.djangoproject.com/ticket/27419
        #   https://github.com/jpwatts/django-positions/issues/49
        #
        deferred_set = super(PersonContact, self).get_deferred_fields()
        return {f for f in deferred_set if f != "name"}

    def save(self, *args, **kwargs):
        if self.user_id and not self.pk:  # Copy things
            user = self.user
            if not self.name:
                self.name = user.get_full_name()
            if not self.email:
                self.email = getattr(user, 'email', '')
            if not self.first_name and not self.last_name:
                self.first_name = getattr(user, 'first_name', '')
                self.last_name = getattr(user, 'last_name', '')

        return super(PersonContact, self).save(*args, **kwargs)

    @cached_property
    def is_all_seeing(self):
        return is_user_all_seeing(self.user)


class AnonymousContact(Contact):
    pk = id = None
    is_anonymous = True
    default_contact_group_identifier = DEFAULT_ANONYMOUS_GROUP_IDENTIFIER
    default_contact_group_name = _("Anonymous Contacts")

    class Meta:
        managed = False  # This isn't something that should actually exist in the database

    def __init__(self, *args, **kwargs):
        super(AnonymousContact, self).__init__(*args, **kwargs)

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
        """
        Contact groups accessor for anonymous contact.

        The base class already has a `groups` property via `ContactGroup`
        related_name, but this overrides it for `AnonymousContact` so that
        it will return a queryset containing just the anonymous contact
        group rather than returning the original related manager, which
        cannot work since `AnonymousContact` is not in the database.

        This allows to use statements like this for all kinds of contacts,
        even `AnonymousContact`::

            some_contact.groups.all()

        :rtype: django.db.QuerySet
        """
        self.get_default_group()  # Make sure group exists
        return ContactGroup.objects.filter(identifier=self.default_contact_group_identifier)


def _split_name(full_name):
    names = full_name.rsplit(" ", 1)
    return (names if len(names) == 2 else [full_name, ""])


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

    if should_force_anonymous_contact(user):
        return AnonymousContact()

    defaults = {
        'is_active': user.is_active,
        'first_name': getattr(user, 'first_name', ''),
        'last_name': getattr(user, 'last_name', ''),
        'email': getattr(user, 'email', ''),
    }
    return PersonContact.objects.get_or_create(user=user, defaults=defaults)[0]


def get_company_contact(user):
    """
    Get preferred CompanyContact of given user.

    If user has associated PersonContact which is member of
    CompanyContact, return CompanyContact. Otherwise, return None.

    :param user: User object (or None) to get contact for
    :type user: django.contrib.auth.models.User|None
    :return:
      CompanyContact (or none) of which user's PersonContact is a member
    :rtype: CompanyContact|None
    """
    if should_force_person_contact(user):
        return None

    contact = get_person_contact(user)
    if not contact:
        return None
    return contact.company_memberships.filter(is_active=True).first()


def get_company_contact_for_shop(shop):
    company = CompanyContact.objects.get_or_create(
        identifier="shop-contact-%s" % shop.pk, defaults={"name": shop.public_name}
    )[0]
    company.shops.add(shop)
    return company


def get_company_contact_for_shop_staff(shop, user):
    assert user.is_staff
    if not getattr(user, "is_superuser", False):
        assert shop.staff_members.filter(id=user.id).exists()

    contact = get_company_contact_for_shop(shop)
    contact.members.add(get_person_contact(user))
    return contact


CompanyContactLogEntry = define_log_model(CompanyContact)
PersonContactLogEntry = define_log_model(PersonContact)
ContactGroupLogEntry = define_log_model(ContactGroup)
