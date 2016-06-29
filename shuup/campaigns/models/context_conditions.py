# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel

from shuup.core.models import AnonymousContact, Contact, ContactGroup


class ContextCondition(PolymorphicModel):
    model = None
    identifier = "context_condition"
    name = _("Context Condition")
    description = _("Context Condition")

    active = models.BooleanField(default=True)

    def matches(self, context):
        return False


class ContactGroupCondition(ContextCondition):
    model = ContactGroup
    identifier = "contact_group_condition"
    name = _("Contact Group")

    contact_groups = models.ManyToManyField(ContactGroup, verbose_name=_("contact groups"))

    def matches(self, context):
        customer = (context.customer if context.customer is not None else AnonymousContact())
        customers_groups = customer.groups.all()
        return self.contact_groups.filter(pk__in=customers_groups).exists()

    @property
    def description(self):
        return _("Limit the campaign to members of the selected contact groups.")

    @property
    def values(self):
        return self.contact_groups

    @values.setter
    def values(self, values):
        self.contact_groups = values


class ContactCondition(ContextCondition):
    model = Contact
    identifier = "contact_condition"
    name = _("Contact")

    contacts = models.ManyToManyField(Contact, verbose_name=_("contacts"))

    def matches(self, context):
        customer = context.customer
        return bool(customer and self.contacts.filter(pk=customer.pk).exists())

    @property
    def description(self):
        return _("Limit the campaign to selected contacts.")

    @property
    def values(self):
        return self.contacts

    @values.setter
    def values(self, values):
        self.contacts = values
