# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.forms import DecimalField, Field, MultipleChoiceField, Select, SelectMultiple
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from numbers import Number


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
            attrs["min"] = self.min_value * self.MULTIPLIER
        if self.max_value is not None:
            attrs["max"] = self.max_value * self.MULTIPLIER
        return attrs


class Select2ModelField(Field):
    """
    This form field class is deprecated and it will be removed on version 3.
    Use ObjectSelect2ModelField class instead.
    """

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
            attrs["data-placeholder"] = _("Select an option")
        return attrs


class Select2MultipleField(Field):
    """
    This form field class is deprecated and it will be removed on version 3.
    Use ObjectSelect2MultipleField class instead.
    """

    widget = SelectMultiple

    def __init__(self, model, search_mode=None, *args, **kwargs):
        self.model = model
        if search_mode:
            self.search_mode = search_mode
        super(Select2MultipleField, self).__init__(*args, **kwargs)

    def prepare_value(self, value):
        values = [getattr(v, "pk", v) for v in value or []]
        # make sure to add the initial values as choices to the field
        if values and not self.widget.choices:
            from django.utils.encoding import force_text

            self.widget.choices = [
                (instance.pk, force_text(instance)) for instance in self.model.objects.filter(pk__in=values)
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
        if getattr(self, "search_mode", None):
            attrs.update({"data-search-mode": self.search_mode})
        if not self.required:
            attrs["data-allow-clear"] = "true"
        return attrs


class Select2ModelMultipleField(Select2MultipleField):
    """
    Just like Select2MultipleField, but return instances instead of ids.

    This form field class is deprecated and it will be removed on version 3.
    Use ObjectSelect2ModelMultipleField class instead.
    """

    def prepare_value(self, value):
        return [getattr(v, "pk", v) for v in value or []]

    def to_python(self, value):
        if value and isinstance(value, (list, tuple)):
            value = [v for v in value if v]
            if value:
                return self.model.objects.filter(pk__in=value)
        return []


class Select2MultipleMainProductField(Select2MultipleField):
    """
    Search only from parent and normal products.

    This form field class is deprecated and it will be removed on version 3.
    Use ObjectSelect2MultipleMainProductField class instead.
    """

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

        return [force_text(v) if v is not None else "" for v in value]


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

    def __init__(self, choices=(), required=True, widget=None, label=None, initial=None, help_text="", *args, **kwargs):
        if not choices:
            choices = self.DAYS_OF_THE_WEEK

        super().__init__(
            choices=choices,
            required=required,
            widget=widget,
            label=label,
            initial=initial,
            help_text=help_text,
            **kwargs
        )

    def clean(self, value):
        return ",".join(super(WeekdayField, self).clean(value))


class ObjectSelect2ModelField(Select2ModelField):
    """
    Class for select2 form fields.
    Replacement for the class Select2ModelField.
    """

    def __init__(self, model, selector=None, search_mode=None, *args, **kwargs):
        super(ObjectSelect2ModelField, self).__init__(model, *args, **kwargs)
        self.selector = selector

    def prepare_value(self, value):
        if self.model:
            return super(ObjectSelect2ModelField, self).prepare_value(value)
        return value

    def to_python(self, value):
        if self.model:
            return super(ObjectSelect2ModelField, self).to_python(value)
        return value

    def widget_attrs(self, widget):
        if self.model:
            attrs = super(ObjectSelect2ModelField, self).widget_attrs(widget)
        else:
            attrs = super(Select2ModelField, self).widget_attrs(widget)
            attrs["data-model"] = self.selector
            if not self.required:
                attrs["data-allow-clear"] = "true"
                attrs["data-placeholder"] = _("Select an option")
        attrs["class"] = "object-selector"
        return attrs


class ObjectSelect2MultipleField(Select2MultipleField):
    """
    Class for select2 form fields.
    Replacement for the class Select2MultipleField.
    """

    def __init__(self, model, selector=None, search_mode=None, *args, **kwargs):
        super(ObjectSelect2MultipleField, self).__init__(model, *args, **kwargs)
        self.selector = selector

    def prepare_value(self, value):
        if self.model:
            return super(ObjectSelect2MultipleField, self).prepare_value(value)
        return value

    def to_python(self, value):
        if self.model:
            return super(ObjectSelect2MultipleField, self).to_python(value)
        if not value:
            return []
        elif not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages["invalid_list"], code="invalid_list")
        return [str(val) for val in value]

    def widget_attrs(self, widget):
        if self.model:
            attrs = super(ObjectSelect2MultipleField, self).widget_attrs(widget)
        else:
            attrs = super(Select2MultipleField, self).widget_attrs(widget)
            attrs["data-model"] = self.selector
            if getattr(self, "search_mode", None):
                attrs.update({"data-search-mode": self.search_mode})
            if not self.required:
                attrs["data-allow-clear"] = "true"
        attrs["class"] = "object-selector"
        return attrs


class ObjectSelect2ModelMultipleField(Select2ModelMultipleField):
    """
    Class for select2 form fields.
    Replacement for the class Select2ModelMultipleField.
    """

    def __init__(self, model, selector=None, search_mode=None, *args, **kwargs):
        super(ObjectSelect2ModelMultipleField, self).__init__(model, *args, **kwargs)
        self.selector = selector

    def prepare_value(self, value):
        if self.model:
            return super(ObjectSelect2ModelMultipleField, self).prepare_value(value)
        return [v for v in value or []]

    def to_python(self, value):
        if self.model:
            return super(ObjectSelect2ModelMultipleField, self).to_python(value)
        if value and isinstance(value, (list, tuple)):
            return value
        return []

    def widget_attrs(self, widget):
        if self.model:
            attrs = super(ObjectSelect2ModelMultipleField, self).widget_attrs(widget)
        else:
            attrs = super(Select2MultipleField, self).widget_attrs(widget)
            attrs["data-model"] = self.selector
            if getattr(self, "search_mode", None):
                attrs.update({"data-search-mode": self.search_mode})
            if not self.required:
                attrs["data-allow-clear"] = "true"
        attrs["class"] = "object-selector"
        return attrs


class ObjectSelect2MultipleMainProductField(Select2MultipleMainProductField):
    """
    Class for select2 form fields.
    Replacement for the class Select2MultipleMainProductField.
    """

    def __init__(self, model, selector=None, search_mode=None, *args, **kwargs):
        super(ObjectSelect2MultipleMainProductField, self).__init__(model, *args, **kwargs)
        self.selector = selector

    def prepare_value(self, value):
        if self.model:
            return super(ObjectSelect2MultipleMainProductField, self).prepare_value(value)
        return [v for v in value or []]

    def to_python(self, value):
        if self.model:
            return super(ObjectSelect2MultipleMainProductField, self).to_python(value)
        if value and isinstance(value, (list, tuple)):
            return value
        return []

    def widget_attrs(self, widget):
        if self.model:
            attrs = super(ObjectSelect2MultipleMainProductField, self).widget_attrs(widget)
        else:
            attrs = super(Select2MultipleField, self).widget_attrs(widget)
            attrs["data-model"] = self.selector
            if getattr(self, "search_mode", None):
                attrs.update({"data-search-mode": self.search_mode})
            if not self.required:
                attrs["data-allow-clear"] = "true"
            return attrs

        attrs["class"] = "object-selector"
        return attrs
