# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import CompanyContact, PersonContact
from shuup.xtheme.layout import Layout
from shuup.xtheme.layout.utils import get_customer_from_context


class AnonymousContactLayout(Layout):
    identifier = "xtheme-anonymous-contact-layout"

    def get_help_text(self, context):
        return _("Content in this box is shown to guests (anonymous users) only.")

    def is_valid_context(self, context):
        customer = get_customer_from_context(context)
        return bool(customer.is_anonymous)

    def get_layout_data_suffix(self, context):
        return self.identifier


class CompanyContactLayout(Layout):
    identifier = "xtheme-company-contact-layout"

    def get_help_text(self, context):
        return _("Content in this box is shown to company contacts only.")

    def is_valid_context(self, context):
        customer = get_customer_from_context(context)
        return isinstance(customer, CompanyContact) if customer else False

    def get_layout_data_suffix(self, context):
        return self.identifier


class ContactLayout(Layout):
    identifier = "xtheme-contact-layout"

    def get_help_text(self, context):
        return _("Content in this box is shown to all logged-in contacts (both person and company; not anonymous).")

    def is_valid_context(self, context):
        customer = get_customer_from_context(context)
        return bool(not customer.is_anonymous)

    def get_layout_data_suffix(self, context):
        return self.identifier


class PersonContactLayout(Layout):
    identifier = "xtheme-person-contact-layout"

    def get_help_text(self, context):
        return _("Content in this box is shown to person contacts only.")

    def is_valid_context(self, context):
        customer = get_customer_from_context(context)
        return isinstance(customer, PersonContact) if customer else False

    def get_layout_data_suffix(self, context):
        return self.identifier
