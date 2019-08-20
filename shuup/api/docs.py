# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.encoding import smart_text
from rest_framework import serializers
from rest_framework.compat import coreapi
from rest_framework.response import Response
from rest_framework.schemas import SchemaGenerator
from rest_framework.schemas.coreapi import AutoSchema, field_to_schema
from rest_framework.utils.formatting import dedent
from rest_framework.views import APIView
from rest_framework_swagger import renderers


class ShuupAPISchema(AutoSchema):
    def _get_method_docstring(self, view, method):
        method_name = getattr(view, 'action', method.lower())
        method_docstring = getattr(view, method_name, None).__doc__
        if method_docstring:
            # An explicit docstring on the method or action.
            return dedent(smart_text(method_docstring))

    def get_description(self, path, method):
        """
        Based on original SchemaGenerator.
        This method take the class docstring directly,
        and put break lines in sections correctly.
        """
        view = self.view
        method_docstring = self._get_method_docstring(view, method)
        if method_docstring:
            return method_docstring

        return super(ShuupAPISchema, self).get_description(path, method)

    def get_serializer_fields(self, path, method):
        """
        Based on original SchemaGenerator, but this looks for
        schema_serializer_class attribute on view.
        The attribute will be available when decorated with `shuup.api.decorators.schema_serializer_class`.
        """
        view = self.view

        if method not in ('PUT', 'PATCH', 'POST'):
            return []

        serializer = None
        if hasattr(view, 'action'):
            serialier_class = getattr(getattr(view, view.action), 'schema_serializer_class', None)
            if serialier_class:
                serializer = serialier_class()
                fields = []
                for field in serializer.fields.values():
                    if field.read_only or isinstance(field, serializers.HiddenField):
                        continue

                    required = field.required and method != 'PATCH'
                    field = coreapi.Field(
                        name=field.field_name,
                        location='form',
                        required=required,
                        schema=field_to_schema(field)
                    )
                    fields.append(field)

                return fields

        return super(ShuupAPISchema, self).get_serializer_fields(path, method)


class JSONOpenAPIRenderer(renderers.OpenAPIRenderer):
    media_type = 'application/json'


class SwaggerSchemaView(APIView):
    renderer_classes = [
        renderers.OpenAPIRenderer,
        renderers.SwaggerUIRenderer,
        JSONOpenAPIRenderer
    ]

    def get(self, request):
        generator = SchemaGenerator(title="Shuup API")
        schema = generator.get_schema(request=request)
        return Response(schema)
