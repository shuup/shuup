# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.db.models import ManyToManyField
from django.utils.translation import ugettext_lazy as _

from shoop.admin.forms import ShoopAdminForm
from shoop.admin.forms.fields import Select2MultipleField


class BaseCampaignForm(ShoopAdminForm):
    class Meta:
        model = None
        exclude = ["identifier", "created_by", "modified_by", "conditions"]

    def __init__(self, **kwargs):
        self.request = kwargs.pop("request")
        self.instance = kwargs.get("instance")
        super(BaseCampaignForm, self).__init__(**kwargs)

    @property
    def service_provider(self):
        return getattr(self.instance, self.service_provider_attr) if self.instance else None

    @service_provider.setter
    def service_provider(self, value):
        setattr(self.instance, self.service_provider_attr, value)

    def clean(self):
        data = super(BaseCampaignForm, self).clean()

        start_datetime = data.get("start_datetime")
        end_datetime = data.get("end_datetime")
        if start_datetime and end_datetime and end_datetime < start_datetime:
            self.add_error("end_datetime", _("Campaign end date can't be before start date."))


class CampaignsSelectMultipleField(Select2MultipleField):
    def __init__(self, campaign_model, *args, **kwargs):
        super(CampaignsSelectMultipleField, self).__init__(
            model=campaign_model.model, label=campaign_model.name,
            help_text=campaign_model.description, *args, **kwargs
        )


class BaseEffectModelForm(forms.ModelForm):
    class Meta:
        exclude = ["identifier", "active"]

    def __init__(self, **kwargs):
        super(BaseEffectModelForm, self).__init__(**kwargs)
        self.fields["campaign"].widget = forms.HiddenInput()
        _process_fields(self, **kwargs)


class BaseRuleModelForm(forms.ModelForm):
    class Meta:
        exclude = ["identifier", "active"]

    def __init__(self, **kwargs):
        super(BaseRuleModelForm, self).__init__(**kwargs)
        _process_fields(self, **kwargs)


def _process_fields(form, **kwargs):
    instance = kwargs.get("instance")
    model_obj = form._meta.model
    for field in model_obj._meta.get_fields(include_parents=False):
        if not isinstance(field, ManyToManyField):
            continue
        if not instance:
            # This happens when before formsets is initialized properly
            # with instance. Let's make the queryset faster.
            form.fields[field.name].queryset = model_obj.model.objects.none()
            continue
        formfield = CampaignsSelectMultipleField(model_obj)
        objects = getattr(instance, field.name).all()
        formfield.required = False
        formfield.widget.choices = [(obj.pk, obj.name) for obj in objects]
        form.fields[field.name] = formfield
