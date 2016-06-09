# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from shuup.core.utils import tax_numbers


class TaxNumberCleanMixin(object):
    company_name_field = "company_name"

    def clean_tax_number(self):
        tax_number = self.cleaned_data["tax_number"].strip()
        if tax_number:
            tax_numbers.validate(tax_number)
        return tax_number

    def clean(self):
        company_name = self.cleaned_data.get(self.company_name_field)
        tax_number = self.cleaned_data.get("tax_number")

        if (not company_name) and (not tax_number):
            return {}
        elif company_name and not tax_number:
            raise ValidationError(_("Tax number required for companies"))
        elif tax_number and not company_name:
            raise ValidationError(_("Cannot use tax number without company name"))

        return self.cleaned_data
