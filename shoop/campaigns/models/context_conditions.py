# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel

from shoop.core.models import ContactGroup


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
    description = _("Contact group")

    contact_groups = models.ManyToManyField(ContactGroup, verbose_name=_("contact groups"))

    @property
    def description(self):
        return _("Limit the campaign to members of the selected contact groups.")

    def matches(self, context):
        if context.customer:
            contact_groups = context.customer.groups.all().values_list("pk", flat=True)
            return self.contact_groups.filter(pk__in=contact_groups).exists()
        return False

    @property
    def values(self):
        return self.contact_groups

    @values.setter
    def values(self, values):
        self.contact_groups = values
