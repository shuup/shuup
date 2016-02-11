# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import OneToOneField
from django.forms import ChoiceField, ModelForm
from django.utils.translation import ugettext_lazy as _

from shoop.admin.forms.fields import PercentageField
from shoop.apps.provides import get_provide_objects
from shoop.campaigns.models.campaigns import (
    BasketCampaign, CatalogCampaign, Coupon
)
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm

CAMPAIGN_COMMON_FIELDS = [
    'name',
    'shop',
    "public_name",
    'discount_percentage',
    'discount_amount_value',
    'active',
    'start_datetime',
    'end_datetime'
]


class CampaignFormMixin(object):
    rule_ids = set()
    existing_rules = []
    rule_field = None
    provide_keys = None

    def _get_values_for_identifier(self, key, identifier):
        """
        Returns values from rule based on the key and the identifier.

        Key can be either `condition` or `filter`.

        `identifier` is an identifier string available in:
          * `shoop.campaigns.basket_conditions.BasketCondition`
          * `shoop.campaigns.catalog_filters.CatalogFilter`
          * `shoop.campaigns.context_conditions.ContextCondition`

        Returns a queryset of objects or a single value found from conditions or filters.
        Returns `None` if nothing is found
        """
        object_set = getattr(self.instance, "%ss" % key)
        for condition_or_filter in object_set.all():
            if condition_or_filter.identifier == identifier:
                if condition_or_filter.model:
                    return condition_or_filter.values.all()
                else:
                    return condition_or_filter.value

    def get_initial_value(self, identifier):
        if self.instance.pk:
            for key in ["condition", "filter"]:
                if key in identifier:
                    return self._get_values_for_identifier(key, identifier)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(CampaignFormMixin, self).__init__(*args, **kwargs)

        for provide_key in self.provide_keys:
            for cls in sorted(get_provide_objects(provide_key), key=lambda x: x.name):
                obj = cls()
                if obj.identifier in self.fields:
                    continue

                for field in obj._meta.get_fields(include_parents=False):
                    if isinstance(field, OneToOneField):
                        continue

                    kwargs = {
                        "initial": self.get_initial_value(obj.identifier),
                        "required": False,  # rules are not required by default, validation is made later on
                        "help_text": obj.description
                    }
                    self.rule_ids.add(obj.identifier)
                    self.fields[obj.identifier] = field.formfield(**kwargs)

    def clean(self):
        """ Ensure at least one rule is set """
        data = super(CampaignFormMixin, self).clean()
        if data.get("discount_percentage") and data.get("discount_amount_value"):
            raise ValidationError(_("You should only define either discount percentage or amount."))

        if not any([data.get("discount_percentage"), data.get("discount_amount_value")]):
            raise ValidationError(_("You must define discount percentage or amount."))

        start_datetime = data.get("start_datetime")
        end_datetime = data.get("end_datetime")
        if start_datetime and end_datetime and end_datetime < start_datetime:
            raise ValidationError(_("Campaign end date can't be before start date."), code="end_is_before_start")

        return data

    def clean_discount_percentage(self):
        percentage = self.cleaned_data.get("discount_percentage", 0)
        if percentage and percentage < 0:
            raise ValidationError(_("Discount percentage cannot be negative."))
        return percentage

    def clean_discount_amount_value(self):
        amount = self.cleaned_data.get("discount_amount_value", 0)
        if amount and amount < 0:
            raise ValidationError(_("Discount amount cannot be negative."))
        return amount

    def save(self, commit=True):
        instance = super(CampaignFormMixin, self).save(commit)
        if self.cleaned_data.get("coupon"):
            instance.coupon = Coupon.objects.get(pk=self.cleaned_data.get("coupon"))

        if hasattr(instance, "conditions"):
            instance.conditions.clear()

        if hasattr(instance, "filters"):
            instance.filters.clear()

        instance.save()

        for provide_key in self.provide_keys:
            for cls in get_provide_objects(provide_key):
                if not self.cleaned_data[cls.identifier]:
                    continue

                field_value = self.cleaned_data[cls.identifier]
                rule = cls.objects.create()
                if rule.model:
                    rule.values = rule.model.objects.filter(pk__in=field_value)
                else:
                    rule.value = field_value
                rule.save()
                if "condition" in cls.identifier:  # a bit weak but to rely this
                    instance.conditions.add(rule)
                else:
                    instance.filters.add(rule)

        instance.save()

        if not instance.created_by:
            instance.created_by = self.request.user
            instance.modified_by = self.request.user
            instance.save()

        return instance


class CatalogCampaignForm(CampaignFormMixin, MultiLanguageModelForm):
    provide_keys = ["campaign_catalog_filter", "campaign_context_condition"]

    discount_percentage = CatalogCampaign._meta.get_field("discount_percentage").formfield(form_class=PercentageField)

    class Meta:
        model = CatalogCampaign
        fields = CAMPAIGN_COMMON_FIELDS

    def clean(self):
        data = super(CatalogCampaignForm, self).clean()
        any_rules_set = any([data.get(rule_field, False) for rule_field in self.rule_ids])
        if not any_rules_set:
            raise ValidationError(_("You must set at least one rule for this campaign."), code="no_rules_set")
        return data


class BasketCampaignForm(CampaignFormMixin, MultiLanguageModelForm):
    provide_keys = ["campaign_basket_condition"]

    discount_percentage = CatalogCampaign._meta.get_field("discount_percentage").formfield(form_class=PercentageField)

    class Meta:
        model = BasketCampaign
        fields = CAMPAIGN_COMMON_FIELDS

    def __init__(self, *args, **kwargs):
        super(BasketCampaignForm, self).__init__(*args, **kwargs)

        # TODO (campaigns): add only those that are not being used
        coupon_code_choices = [('', '')] + list(Coupon.objects.filter(active=True).values_list("pk", "code"))
        field_kwargs = dict(choices=coupon_code_choices, required=False)
        field_kwargs["help_text"] = _("Define the required coupon for this campaign.")
        if self.instance.pk and self.instance.coupon:
            field_kwargs["initial"] = self.instance.coupon.pk

        self.fields["coupon"] = ChoiceField(**field_kwargs)

    def clean(self):
        """ Ensure atleast one rule is set """
        data = super(BasketCampaignForm, self).clean()
        any_rules_set = any([data.get(rule_field, False) for rule_field in self.rule_ids])
        if not any_rules_set and self.cleaned_data.get("coupon"):
            any_rules_set = True

        if not any_rules_set:
            raise ValidationError(
                _("You must set atleast one rule or discount code for this campaign."),
                code="no_rules_set")
        return data


class CouponForm(ModelForm):
    autogenerate = forms.BooleanField(label=_("Autogenerate code"), required=False)

    class Meta:
        model = Coupon
        fields = [
            'code',
            'usage_limit_customer',
            'usage_limit',
            'active'
        ]

    def __init__(self, *args, **kwargs):
        super(CouponForm, self).__init__(*args, **kwargs)
        if self.instance.pk and self.instance.has_been_used():
            self.fields["code"].readonly = True

    def clean_code(self):
        code = self.cleaned_data["code"]
        qs = Coupon.objects.filter(code=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(_("Discount Code already in use."))
        return code
