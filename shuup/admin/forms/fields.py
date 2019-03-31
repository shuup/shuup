# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal
from numbers import Number

from django.forms import (
    DecimalField, Field, MultipleChoiceField, Select, SelectMultiple
)
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _


class PercentageField(DecimalField):
    MULTIPLIER = Decimal(100)

    def prepare_value(self, value):
        # Percentage values are 0..1 in database, so multiply by 100
        if value is not None and isinstance(value, Number):
            value *= self.MULTIPLIER
        return super(PercentageField, self).prepare_value(value)

    def to_python(self, value):
        value = super(PercentageField, self).to_python(value)
        if value is not None:
            # We got a value, so divide it by 100 to get the 0..1 range value
            value /= self.MULTIPLIER
        return value

    def widget_attrs(self, widget):
        attrs = super(PercentageField, self).widget_attrs(widget)
        if self.min_value is not None:
            attrs['min'] = self.min_value * self.MULTIPLIER
        if self.max_value is not None:
            attrs['max'] = self.max_value * self.MULTIPLIER
        return attrs


class Select2ModelField(Field):
    widget = Select

    def __init__(self, model, *args, **kwargs):
        self.model = model
        super(Select2ModelField, self).__init__(*args, **kwargs)

    def prepare_value(self, value):
        return getattr(value, "pk", value)

    def to_python(self, value):
        if value:
            return self.model.objects.filter(pk=value).first()

    def widget_attrs(self, widget):
        attrs = super(Select2ModelField, self).widget_attrs(widget)
        model_name = "%s.%s" % (self.model._meta.app_label, self.model._meta.model_name)
        attrs.update({"data-model": model_name})
        if not self.required:
            attrs["data-allow-clear"] = "true"
        return attrs


class Select2MultipleField(Field):
    widget = SelectMultiple

    def __init__(self, model, *args, **kwargs):
        self.model = model
        super(Select2MultipleField, self).__init__(*args, **kwargs)

    def prepare_value(self, value):
        values = [getattr(v, "pk", v) for v in value or []]
        # make sure to add the initial values as choices to the field
        if values and not self.widget.choices:
            from django.utils.encoding import force_text
            self.widget.choices = [
                (instance.pk, force_text(instance))
                for instance in self.model.objects.filter(pk__in=values)
            ]
        return values

    def to_python(self, value):
        value = super(Select2MultipleField, self).to_python(value)
        # Here we have sometimes None which will cause errors when
        # saving related fields so let's fallback to empty list
        return value or []

    def widget_attrs(self, widget):
        attrs = super(Select2MultipleField, self).widget_attrs(widget)
        model_name = "%s.%s" % (self.model._meta.app_label, self.model._meta.model_name)
        attrs.update({"data-model": model_name})
        if not self.required:
            attrs["data-allow-clear"] = "true"
        return attrs


class Select2ModelMultipleField(Select2MultipleField):
    """
    Just like Select2MultipleField, but return instances instead of ids
    """
    def prepare_value(self, value):
        return [getattr(v, "pk", v) for v in value or []]

    def to_python(self, value):
        if value:
            return self.model.objects.filter(pk__in=value)
        return []


class Select2MultipleMainProductField(Select2MultipleField):
    """Search only from parent and normal products"""
    def widget_attrs(self, widget):
        attrs = super(Select2MultipleMainProductField, self).widget_attrs(widget)
        attrs.update({"data-search-mode": "main"})
        return attrs


class WeekdaysSelectMultiple(SelectMultiple):
    def format_value(self, value):
        if value is None and self.allow_multiple_selected:
            return []

        if isinstance(value, str):
            value = value.split(",")

        if not isinstance(value, (tuple, list)):
            value = [value]

        return [force_text(v) if v is not None else '' for v in value]


class WeekdayField(MultipleChoiceField):
    widget = WeekdaysSelectMultiple

    DAYS_OF_THE_WEEK = [
        (0, _("Monday")),
        (1, _("Tuesday")),
        (2, _("Wednesday")),
        (3, _("Thursday")),
        (4, _("Friday")),
        (5, _("Saturday")),
        (6, _("Sunday")),
    ]

    def __init__(self, choices=(), required=True, widget=None, label=None, initial=None, help_text='', *args, **kwargs):
        if not choices:
            choices = self.DAYS_OF_THE_WEEK
        super(WeekdayField, self).__init__(choices, required, widget, label, initial, help_text, *args, **kwargs)

    def clean(self, value):
        return ",".join(super(WeekdayField, self).clean(value))
