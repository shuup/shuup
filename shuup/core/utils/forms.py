# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from collections import OrderedDict

from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Contact, ImmutableAddress, MutableAddress
from shuup.utils.iterables import first


class MutableAddressForm(forms.ModelForm):
    class Meta:
        model = MutableAddress
        fields = (
            "name", "name_ext", "phone", "email",
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
        if self.instance.pk:
            if isinstance(self.instance, ImmutableAddress) or _is_assigned_multiple_times(self.instance):
                self.instance.pk = None  # Force resave
        return super(MutableAddressForm, self).save(commit)


def _is_assigned_multiple_times(address):
    contacts_assigned_to_count = Contact.objects.filter(
        Q(default_billing_address_id=address.id) | Q(default_shipping_address_id=address.id)).count()
    if contacts_assigned_to_count != 1:
        return bool(contacts_assigned_to_count)
    contact_assigned_to = Contact.objects.filter(
        Q(default_billing_address_id=address.id) | Q(default_shipping_address_id=address.id)).first()
    return bool(contact_assigned_to.default_billing_address_id == contact_assigned_to.default_shipping_address_id)


class FormInfoMap(OrderedDict):
    def __init__(self, form_classes):
        form_infos = (FormInfo(formcls) for formcls in form_classes)
        super(FormInfoMap, self).__init__(
            (form_info.choice_value, form_info) for form_info in form_infos)

    def get_by_object(self, obj):
        return first(
            form_info for form_info in self.values() if isinstance(obj, form_info.model))

    def get_by_choice_value(self, choice_value):
        return self.get(choice_value)

    def get_type_choices(self):
        return [(x.choice_value, x.choice_text) for x in self.values()]


class FormInfo(object):
    def __init__(self, form_class):
        self.form_class = form_class
        self.model = form_class._meta.model
        model_meta = self.model._meta
        self.choice_value = model_meta.app_label + '.' + model_meta.model_name
        self.choice_text = model_meta.verbose_name.capitalize()
