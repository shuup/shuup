# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from collections import Counter

import six
from django.utils.encoding import force_text, smart_text
from parler_rest.fields import TranslatedFieldsField
from rest_framework import serializers
from rest_framework.compat import coreapi
from rest_framework.response import Response
from rest_framework.schemas import (
    formatting, header_regex, SchemaGenerator, types_lookup
)
from rest_framework.views import APIView, get_view_description
from rest_framework_swagger import renderers

from shuup.api.fields import EnumField


def guess_field_type(field):
    """
    Tries to guess the field type.
    Fallbacks to original rest_framework.schemas.types_lookup dict

    :param rest_framework.fields.Field field: the serializer field to guess the type
    """

    if isinstance(field, TranslatedFieldsField):
        return 'object'

    elif isinstance(field, EnumField):
        # take all the choices and count the most common type of the enum
        types = Counter([type(x) for x in field.choices])
        most_common = types.most_common(1)[0][0]

        # we can only check for string, numbers and boolean constants
        # otherwise we dont't know that it is
        if most_common in six.string_types or most_common == six.text_type:
            return "string"
        elif most_common in six.integer_types:
            return "number"
        elif most_common == bool:
            return "boolean"

    return types_lookup[field]


class ShuupAPISchemaGenerator(SchemaGenerator):

    def _get_method_docstring(self, view, method):
        method_name = getattr(view, 'action', method.lower())
        method_docstring = getattr(view, method_name, None).__doc__
        if method_docstring:
            # An explicit docstring on the method or action.
            return formatting.dedent(smart_text(method_docstring))

    def get_description(self, path, method, view):
        """
        Based on original SchemaGenerator.
        This method take the class docstring directly,
        and put break lines in sections correctly.
        """
        method_docstring = self._get_method_docstring(view, method)
        if method_docstring:
            return method_docstring

        description = get_view_description(view.__class__)
        lines = [line.strip() for line in description.splitlines()]
        current_section = ''
        sections = {'': ''}

        for line in lines:
            if header_regex.match(line):
                current_section, _, lead = line.partition(':')
                sections[current_section] = lead.strip()
            else:
                sections[current_section] += '\n' + line

        header = getattr(view, 'action', method.lower())
        if header in sections:
            return sections[header].strip()
        if header in self.coerce_method_names:
            if self.coerce_method_names[header] in sections:
                return sections[self.coerce_method_names[header]].strip()
        return sections[''].strip()

    def get_serializer_fields(self, path, method, view):
        """
        Based on original SchemaGenerator, but this looks for
        schema_serializer_class attribute on view.
        The attribute will be available when decorated with `shuup.api.decorators.schema_serializer_class`.
        """

        if method not in ('PUT', 'PATCH', 'POST'):
            return []

        serializer = None

        if hasattr(view, 'action'):
            serialier_class = getattr(getattr(view, view.action), 'schema_serializer_class', None)
            if serialier_class:
                serializer = serialier_class()

        if not serializer and hasattr(view, 'get_serializer'):
            serializer = view.get_serializer()

        if not serializer:
            return []

        if isinstance(serializer, serializers.ListSerializer):
            return [
                coreapi.Field(
                    name='data',
                    location='body',
                    required=True,
                    type='array'
                )
            ]

        if not isinstance(serializer, serializers.Serializer):
            return []

        fields = []
        for field in serializer.fields.values():
            if field.read_only or isinstance(field, serializers.HiddenField):
                continue

            required = field.required and method != 'PATCH'
            description = force_text(field.help_text) if field.help_text else ''
            field = coreapi.Field(
                name=field.field_name,
                location='form',
                required=required,
                description=description,
                type=guess_field_type(field)
            )
            fields.append(field)

        return fields


class JSONOpenAPIRenderer(renderers.OpenAPIRenderer):
    media_type = 'application/json'


class SwaggerSchemaView(APIView):
    renderer_classes = [
        renderers.OpenAPIRenderer,
        renderers.SwaggerUIRenderer,
        JSONOpenAPIRenderer
    ]

    def get(self, request):
        generator = ShuupAPISchemaGenerator(title="Shuup API")
        schema = generator.get_schema(request=request)
        return Response(schema)
