# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shoop.admin.form_part import FormPart, TemplatedFormDef
from shoop.campaigns.models import ContactGroupSalesRange
from shoop.core.models import Shop, ShopStatus
from shoop.core.models._contacts import PROTECTED_CONTACT_GROUP_IDENTIFIERS


class SalesRangesForm(forms.ModelForm):
    class Meta:
        model = ContactGroupSalesRange
        fields = ["min_value", "max_value"]
        labels = {
            "min_value": _("Minimum value"),
            "max_value": _("Maximum value")
        }
        help_texts = {
            "max_value": _("Leave empty for no maximum")
        }

    def __init__(self, **kwargs):
        super(SalesRangesForm, self).__init__(**kwargs)


class SalesRangesFormPart(FormPart):
    priority = 3
    name = "contact_group_sales_ranges"
    form = SalesRangesForm

    def __init__(self, request, object=None):
        super(SalesRangesFormPart, self).__init__(request, object)
        self.shops = Shop.objects.filter(status=ShopStatus.ENABLED)

    def _get_form_name(self, shop):
        return "%d-%s" % (shop.pk, self.name)

    def get_form_defs(self):
        if not self.object.pk or self.object.identifier in PROTECTED_CONTACT_GROUP_IDENTIFIERS:
            return

        for shop in self.shops:
            instance, _ = ContactGroupSalesRange.objects.get_or_create(group=self.object, shop=shop)
            yield TemplatedFormDef(
                name=self._get_form_name(shop),
                form_class=self.form,
                template_name="shoop/campaigns/admin/sales_ranges_form_part.jinja",
                required=False,
                kwargs={"instance": instance}
            )

    def form_valid(self, form):
        form_names = [self._get_form_name(shop) for shop in self.shops]
        forms = [form.forms[name] for name in form_names if name in form.forms]
        for form in forms:
            if form.changed_data:
                form.save()
