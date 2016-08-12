# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import Select2MultipleField
from shuup.core.models import Contact
from shuup.reports.forms import BaseReportForm


class OrderReportForm(BaseReportForm):

    def __init__(self, *args, **kwargs):
        super(OrderReportForm, self).__init__(*args, **kwargs)

        customer_field = Select2MultipleField(label=_("Customer"), model=Contact, required=False)
        customers = self.initial_contacts("customer")
        if customers:
            customer_field.initial = customers
            customer_field.widget.choices = [(obj.pk, obj.name) for obj in customers]

        orderer_field = Select2MultipleField(label=_("Orderer"), model=Contact, required=False)
        orderers = self.initial_contacts("orderer")
        if orderers:
            orderer_field.initial = orderers
            orderer_field.widget.choices = [(obj.pk, obj.name) for obj in orderers]

        self.fields["customer"] = customer_field
        self.fields["orderer"] = orderer_field

    def initial_contacts(self, key):
        if self.data and key in self.data:
            return Contact.objects.filter(pk__in=self.data.getlist(key))
        return []
