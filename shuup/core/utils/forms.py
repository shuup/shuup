# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import ImmutableAddress, MutableAddress


class MutableAddressForm(forms.ModelForm):
    class Meta:
        model = MutableAddress
        fields = (
            "name", "phone", "email",
            "street", "street2", "postal_code", "city",
            "region", "region_code", "country"
        )
        labels = {
            "region_code": _("Region")
        }

    def __init__(self, **kwargs):
        super(MutableAddressForm, self).__init__(**kwargs)
        if not kwargs.get("instance"):
            # Set default country
            self.fields["country"].initial = settings.SHUUP_ADDRESS_HOME_COUNTRY

        field_properties = settings.SHUUP_ADDRESS_FIELD_PROPERTIES
        for field, properties in field_properties.items():
            for prop in properties:
                setattr(self.fields[field], prop, properties[prop])

    def save(self, commit=True):
        if self.instance.pk and isinstance(self.instance, ImmutableAddress):
            self.instance.pk = None  # Force resave
        return super(MutableAddressForm, self).save(commit)
