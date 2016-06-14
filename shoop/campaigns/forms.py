# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import ast

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import ManyToManyField, OneToOneField, Q, QuerySet
from django.forms import ChoiceField, ModelForm
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.admin.forms.widgets import Select2Multiple
from shoop.apps.provides import get_provide_objects
from shoop.campaigns.models.campaigns import (
    BasketCampaign, CatalogCampaign, Coupon
)
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm

CAMPAIGN_COMMON_FIELDS = [
    'name',
    'shop',
    "public_name",
    'active',
    'start_datetime',
    'end_datetime'
]


class CampaignFormMixin(object):
    rule_ids = set()
    effect_ids = set()
    existing_rules = []
    rule_field = None
    provide_keys = []
    effect_keys = []

    def _get_values_for_identifier(self, key, identifier):
        """
        Returns values from rule or effect based on the key and the identifier.

        Key can be either `condition` or `filter`.

        `identifier` is an identifier string available in:
          * `shoop.campaigns.basket_conditions.BasketCondition`
          * `shoop.campaigns.catalog_filters.CatalogFilter`
          * `shoop.campaigns.context_conditions.ContextCondition`
          * `shoop.campaigns.basket_effects.BasketDiscountEffect`
          * `shoop.campaigns.product_effects.ProductDiscountEffect`

        Returns a queryset of objects or a single value found from conditions, filters or effects.
        Returns `None` if nothing is found
        """
        object_set = getattr(self.instance, "%ss" % key)
        for obj in object_set.all():
            if obj.identifier == identifier:
                if obj.model:
                    return obj.values.all()
                else:
                    return obj.value

    def get_initial_value(self, identifier):
        if self.instance.pk:
            for key in ["condition", "filter", "effect"]:
                if key in identifier:
                    return self._get_values_for_identifier(key, identifier)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(CampaignFormMixin, self).__init__(*args, **kwargs)

        for provide_key in self.provide_keys:
            self._add_fields(provide_key)

        for provide_key in self.effect_keys:
            self._add_fields(provide_key, False)

    def _add_fields(self, provide_key, is_provide=True):
        for cls in sorted(get_provide_objects(provide_key), key=lambda x: x.name):
            obj = cls()
            if obj.identifier in self.fields:
                continue

            for field in obj._meta.get_fields(include_parents=False):
                if isinstance(field, OneToOneField):
                    continue

                if is_provide:
                    self.rule_ids.add(obj.identifier)
                else:
                    self.effect_ids.add(obj.identifier)

                kwargs = {
                    "required": False,  # rules are not required by default, validation is made later on
                    "help_text": obj.description
                }

                if hasattr(obj, "admin_form_class") and obj.admin_form_class:
                    kwargs.update({
                        "form_class": obj.admin_form_class
                    })

                if isinstance(field, ManyToManyField):
                    kwargs.update({
                        "initial": self._get_many_to_many_initial_values(obj),
                        "widget": Select2Multiple(model=obj.model)
                    })
                    formfield = forms.CharField(**kwargs)
                    value = kwargs.get("initial")
                    if value:
                        formfield.widget.choices = [
                            (object.pk, force_text(object)) for object in obj.model.objects.filter(pk__in=value)]
                else:
                    kwargs.update({
                        "initial": self.get_initial_value(obj.identifier)
                    })
                    formfield = field.formfield(**kwargs)

                self.fields[obj.identifier] = formfield

    def _get_many_to_many_initial_values(self, obj):
        initial_value = self.get_initial_value(obj.identifier)
        if initial_value is None:
            return None
        elif isinstance(initial_value, QuerySet):
            return [x.pk for x in initial_value]
        else:
            return [initial_value]

    def clean(self):
        data = super(CampaignFormMixin, self).clean()

        # Ensure at least 1 effect is set
        effect_count = 0
        for key in self.effect_keys:
            for cls in get_provide_objects(key):
                if data[cls.identifier]:
                    effect_count += 1

                if effect_count > 1:
                    raise ValidationError(_("You should only define one effect."))
        if not effect_count:
            raise ValidationError(_("At least one effect must be defined."))

        start_datetime = data.get("start_datetime")
        end_datetime = data.get("end_datetime")
        if start_datetime and end_datetime and end_datetime < start_datetime:
            raise ValidationError(_("Campaign end date can't be before start date."), code="end_is_before_start")

        return data

    def save(self, commit=True):
        instance = super(CampaignFormMixin, self).save(commit)
        if self.cleaned_data.get("coupon"):
            instance.coupon = Coupon.objects.get(pk=self.cleaned_data.get("coupon"))

        if hasattr(instance, "conditions"):
            instance.conditions.clear()

        if hasattr(instance, "filters"):
            instance.filters.clear()

        if hasattr(instance, "effects"):
            instance.effects.all().delete()

        instance.save()

        for provide_key in self.provide_keys:
            self._save_conditions_and_filters(provide_key, instance)

        for effect_key in self.effect_keys:
            self._save_effects(effect_key, instance)

        instance.save()

        if not instance.created_by:
            instance.created_by = self.request.user
            instance.modified_by = self.request.user
            instance.save()

        return instance

    def _save_effects(self, effect_key, instance):
        for cls in get_provide_objects(effect_key):
            if not self.cleaned_data[cls.identifier]:
                continue
            field_value = self.cleaned_data[cls.identifier]
            effect = cls.objects.create(campaign=instance)
            if effect.model:
                effect.values = effect.model.objects.filter(pk__in=ast.literal_eval(field_value))
            else:
                effect.value = field_value
            effect.campaign = instance
            effect.save()

    def _save_conditions_and_filters(self, provide_key, instance):
        for cls in get_provide_objects(provide_key):
            if not self.cleaned_data[cls.identifier]:
                continue

            field_value = self.cleaned_data[cls.identifier]
            rule = cls.objects.create()
            if rule.model:
                rule.values = rule.model.objects.filter(pk__in=ast.literal_eval(field_value))
            else:
                rule.value = field_value
            rule.save()
            if "condition" in cls.identifier:  # a bit weak but to rely this
                instance.conditions.add(rule)
            else:
                instance.filters.add(rule)


class CatalogCampaignForm(CampaignFormMixin, MultiLanguageModelForm):
    provide_keys = ["campaign_catalog_filter", "campaign_context_condition"]
    effect_keys = ["catalog_campaign_effect"]

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
    effect_keys = ["basket_campaign_effect"]

    class Meta:
        model = BasketCampaign
        fields = CAMPAIGN_COMMON_FIELDS

    def __init__(self, *args, **kwargs):
        super(BasketCampaignForm, self).__init__(*args, **kwargs)

        coupon_code_choices = [('', '')] + list(
            Coupon.objects.filter(
                Q(active=True),
                Q(campaign=None) | Q(campaign=self.instance)
            ).values_list("pk", "code")
        )
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
