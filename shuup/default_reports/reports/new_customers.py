# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _
from operator import itemgetter

from shuup.core.models import Contact
from shuup.default_reports.forms import NewCustomersReportForm
from shuup.reports.report import ShuupReportBase


class NewCustomersReport(ShuupReportBase):
    identifier = "new_customers_report"
    title = _("New Customers")
    form_class = NewCustomersReportForm

    filename_template = "new-customers-report-%(time)s"
    schema = [
        {"key": "date", "title": _("Date")},
        {"key": "personcontact", "title": _("Persons")},
        {"key": "companycontact", "title": _("Companies")},
        {"key": "users", "title": _("Users")},
    ]

    def get_data(self):
        contacts = (
            Contact.objects.filter(created_on__range=(self.start_date, self.end_date))
            .select_related("polymorphic_ctype")
            .order_by("created_on")[: self.queryset_row_limit]
        )

        data = {}
        users = set()

        for contact in contacts:
            created_on = contact.created_on.strftime(self.options["group_by"])
            model = contact.polymorphic_ctype.model
            user = getattr(contact, "user_id", 0)

            if created_on not in data:
                data[created_on] = {"date": created_on, "users": 0, "personcontact": 0, "companycontact": 0}

            data[created_on][model] += 1

            if user and user not in users:
                data[created_on]["users"] += 1

        data = sorted(data.values(), key=itemgetter("date"))
        return self.get_return_data(data)
