# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import base64
import binascii
import mimetypes
import uuid

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import six
from django.utils.encoding import force_text
from rest_framework import serializers

from shuup.core.fields import (
    FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES, FORMATTED_DECIMAL_FIELD_MAX_DIGITS
)


class EnumField(serializers.ChoiceField):
    """
    https://github.com/hzdg/django-enumfields/blob/0.9.0/enumfields/drf/fields.py
    """
    def __init__(self, enum, lenient=False, ints_as_names=False, **kwargs):
        """
        :param enum: The enumeration class.
        :param lenient: Whether to allow lenient parsing (case-insensitive, by value or name)
        :type lenient: bool
        :param ints_as_names: Whether to serialize integer-valued enums by their name, not the integer value
        :type ints_as_names: bool
        """
        self.enum = enum
        self.lenient = lenient
        self.ints_as_names = ints_as_names
        kwargs['choices'] = tuple((e.value, getattr(e, 'label', e.name)) for e in self.enum)
        super(EnumField, self).__init__(**kwargs)

    def to_representation(self, instance):
        if instance in ('', u'', None):
            return instance
        try:
            if not isinstance(instance, self.enum):
                instance = self.enum(instance)  # Try to cast it
            if self.ints_as_names and isinstance(instance.value, six.integer_types):
                # If the enum value is an int, assume the name is more representative
                return instance.name.lower()
            return instance.value
        except ValueError:
            raise ValueError('Invalid value [%r] of enum %s' % (instance, self.enum.__name__))

    def to_internal_value(self, data):
        if isinstance(data, self.enum):
            return data
        try:
            # Convert the value using the same mechanism DRF uses
            converted_value = self.choice_strings_to_values[six.text_type(data)]
            return self.enum(converted_value)
        except (ValueError, KeyError):
            pass

        if self.lenient:
            # Normal logic:
            for choice in self.enum:
                if choice.name == data or choice.value == data:
                    return choice

            # Case-insensitive logic:
            l_data = force_text(data).lower()
            for choice in self.enum:
                if choice.name.lower() == l_data or force_text(choice.value).lower() == l_data:
                    return choice

        # Fallback (will likely just raise):
        return super(EnumField, self).to_internal_value(data)


class TypedContentFile(ContentFile):
    def __init__(self, content, content_type, name=None):
        self.content_type = content_type
        super(TypedContentFile, self).__init__(content, name)


class Base64FileField(serializers.FileField):
    """
    Inspired in https://github.com/Hipo/drf-extra-fields/blob/master/drf_extra_fields/fields.py
    But here we use the media type from the header to guess the file type
    """
    def to_internal_value(self, base64_data):
        if not isinstance(base64_data, six.string_types):
            raise ValidationError("This is not a base64 string")

        elif ';base64,' not in base64_data:
            raise ValidationError("base64 files must have media type defined.")

        header, base64_data = base64_data.split(';base64,')

        try:
            decoded_file = base64.b64decode(base64_data)
        except (TypeError, binascii.Error):
            raise ValidationError("Invalid file.")

        media_type = header[len("data:"):]  # remove data: from the start of the string
        extension = mimetypes.guess_extension(media_type, strict=False)
        if not extension:
            raise ValidationError("Media type not recognized.")

        file_name = "{0}{1}".format(uuid.uuid4(), extension)
        data = TypedContentFile(decoded_file, media_type, name=file_name)
        return super(Base64FileField, self).to_internal_value(data)

    def to_representation(self, file):
        try:
            mime_type = mimetypes.guess_type(file.path, strict=False)
            with open(file.path, 'rb') as f:
                return "data:{0};base64,{1}".format(mime_type, base64.b64encode(f.read()).decode())
        except Exception:
            raise IOError("Error encoding file")


class FormattedDecimalField(serializers.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = FORMATTED_DECIMAL_FIELD_MAX_DIGITS
        kwargs['decimal_places'] = FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES
        super(FormattedDecimalField, self).__init__(*args, **kwargs)
