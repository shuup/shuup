# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import enumfields
from django import forms
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import validate_email
from django.utils.text import camel_case_to_spaces
from django.utils.translation import ugettext_lazy as _


class MultiEmailField(forms.Field):
    """
    From https://docs.djangoproject.com/en/1.11/ref/forms/validation/#form-field-default-cleaning
    """
    def validate(self, value):
        """Check if value consists only of valid emails."""
        # Use the parent's handling of required fields, etc.
        super().validate(value)
        if value:
            for email in value.split(','):
                if email:
                    validate_email(email)


class Type(object):
    name = None
    identifier = None

    def get_field(self, **kwargs):
        """
        Get a Django form field for this type.

        The kwargs are passed directly to the field
        constructor.

        :param kwargs: Kwargs for field constructor.
        :type kwargs: dict
        :return: Form field.
        :rtype: django.forms.Field
        """
        return forms.CharField(**kwargs)

    def unserialize(self, value):
        return self.get_field().to_python(value)

    def validate(self, value):
        return self.get_field().validate(value)

    def is_coercible_from(self, other_type):
        return self.identifier == other_type.identifier


class _String(Type):
    pass


class _Number(Type):
    pass


class Boolean(Type):
    name = _("Boolean")
    identifier = "boolean"

    def get_field(self, **kwargs):
        return forms.BooleanField(**kwargs)


class Integer(_Number):
    name = _("Integer Number")
    identifier = "integer"

    def get_field(self, **kwargs):
        return forms.IntegerField(**kwargs)


class Decimal(_Number):
    name = _("Decimal Number")
    identifier = "decimal"

    def get_field(self, **kwargs):
        return forms.DecimalField(**kwargs)


class Text(_String):
    name = _("Text")
    identifier = "text"

    def is_coercible_from(self, other_type):
        # All variables can be used as raw text
        return True


class Language(_String):
    name = _("Language")
    identifier = "language"


class Email(_String):
    name = _("Email Address")
    identifier = "email"

    def get_field(self, **kwargs):
        return MultiEmailField(**kwargs)


class URL(_String):
    name = _("URL Address")
    identifier = "url"

    def get_field(self, **kwargs):
        return forms.URLField(**kwargs)


class Phone(_String):
    name = _("Phone Number")
    identifier = "phone"


class Model(Type):
    model_label = None
    identifier = "model"

    @property
    def name(self):
        return self.get_model()._meta.verbose_name

    def __init__(self, model_label):
        """
        :param model_label: Model label in Django `app.Model` format (e.g. `shuup.Order`).
        :type model_label: str
        """
        self.model_label = model_label

    def unserialize(self, value):
        if isinstance(value, self.get_model()):
            return value

        try:
            return self.get_model().objects.get(pk=value)
        except ObjectDoesNotExist:
            return None

    def is_coercible_from(self, other_type):
        return isinstance(other_type, Model) and self.get_model() == other_type.get_model()

    def get_model(self):
        """
        :rtype: django.db.models.Model
        """
        return apps.get_model(self.model_label)

    def get_field(self, **kwargs):
        kwargs.setdefault("queryset", self.get_model().objects.all())
        return forms.ModelChoiceField(**kwargs)


class Enum(Type):
    enum_class = None
    identifier = "enum"

    @property
    def name(self):
        if self.enum_class:
            return camel_case_to_spaces(self.enum_class.__class__.__name__)
        return u"<Invalid Enum>"

    def __init__(self, enum_class):
        self.enum_class = enum_class
        assert issubclass(enum_class, enumfields.Enum), "%r is not an enum" % enum_class

    def unserialize(self, value):
        if isinstance(value, self.enum_class):
            return value

        try:
            return self.enum_class(value)
        except ValueError:
            try:
                return self.enum_class(int(value))
            except ValueError:
                pass
        return None

    def get_field(self, **kwargs):
        return enumfields.EnumField(self.enum_class).formfield(**kwargs)
