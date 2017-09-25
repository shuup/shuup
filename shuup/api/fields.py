# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import base64
import binascii
import mimetypes
import uuid

import six
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from rest_framework import serializers


class EnumField(serializers.ChoiceField):
    """
    A field which accepts django-enumfields types
    """
    def __init__(self, enum, **kwargs):
        self.enum = enum
        kwargs['choices'] = enum.choices()
        super(EnumField, self).__init__(**kwargs)

    def to_representation(self, obj):
        return obj.value

    def to_internal_value(self, data):
        return self.enum(data)


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
