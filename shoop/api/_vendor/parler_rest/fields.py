# -*- coding: utf-8 -*-

"""Custom serializer fields for nested translations."""

from __future__ import unicode_literals
from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers
from .utils import create_translated_fields_serializer


class TranslatedFieldsField(serializers.Field):

    """Exposing translated fields for a TranslatableModel in REST style."""

    default_error_messages = dict(serializers.Field.default_error_messages, **{
        'invalid': "Input is not a valid dict",
    })

    def __init__(self, *args, **kwargs):
        """Receive custom serializer class and model."""
        self.serializer_class = kwargs.pop('serializer_class', None)
        self.shared_model = kwargs.pop('shared_model', None)
        super(TranslatedFieldsField, self).__init__(*args, **kwargs)

    def bind(self, field_name, parent):
        """Create translation serializer dynamically.

        Takes translatable model class (shared_model) from parent serializer and it
        may create a serializer class on the fly if no custom class was specified.
        """
        super(TranslatedFieldsField, self).bind(field_name, parent)
        # Expect 1-on-1 for now.
        related_name = self.source or field_name

        # This could all be done in __init__(), but by moving the code here,
        # it's possible to auto-detect the parent model.
        if self.shared_model is not None and self.serializer_class is not None:
            return

        # Fill in the blanks
        if self.serializer_class is None:
            # Auto detect parent model
            if self.shared_model is None:
                self.shared_model = parent.Meta.model

            # Create serializer based on shared model.
            translated_model = self.shared_model._parler_meta[related_name]
            self.serializer_class = create_translated_fields_serializer(
                self.shared_model, related_name=related_name,
                meta={'fields': translated_model.get_translated_fields()}
            )
        else:
            self.shared_model = self.serializer_class.Meta.model

            # Don't need to have a 'language_code', it will be split up already,
            # so this should avoid redundant output.
            if 'language_code' in self.serializer_class().fields:
                raise ImproperlyConfigured("Serializer may not have a 'language_code' field")

    def to_representation(self, value):
        """Serialize translated fields.

        Simply iterate over available translations and, for each language,
        delegate serialization logic to the translation model serializer.
        """
        if value is None:
            return

        # Only need one serializer to create the native objects
        serializer = self.serializer_class()

        # Split into a dictionary per language
        result = serializers.OrderedDict()
        for translation in value.all():  # value = translations related manager
            result[translation.language_code] = serializer.to_representation(translation)

        return result

    def to_internal_value(self, data):
        """Deserialize data from translations fields.

        For each received language, delegate validation logic to
        the translation model serializer.
        """
        if data is None:
            return

        if not isinstance(data, dict):
            self.fail('invalid')

        result, errors = {}, {}
        for lang_code, model_fields in data.items():
            serializer = self.serializer_class(data=model_fields)
            if serializer.is_valid():
                result[lang_code] = serializer.data
            else:
                errors[lang_code] = serializer.errors

        if errors:
            raise serializers.ValidationError(errors)
        return result
