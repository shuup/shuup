# -*- coding: utf-8 -*-

"""Various utilities to ease integration with Rest Framework."""

from rest_framework import serializers


def create_translated_fields_serializer(shared_model, meta=None, related_name=None, **fields):
    """Create a Rest Framework serializer class for a translated fields model.

    :param shared_model: The shared model.
    :type shared_model: :class:`parler.models.TranslatableModel`
    """
    if not related_name:
        translated_model = shared_model._parler_meta.root_model
    else:
        translated_model = shared_model._parler_meta[related_name].model

    # Define inner Meta class
    if not meta:
        meta = {}
    meta['model'] = translated_model
    meta.setdefault('fields', ['language_code'] + translated_model.get_translated_fields())

    # Define serialize class attributes
    attrs = {}
    attrs.update(fields)
    attrs['Meta'] = type('Meta', (), meta)

    # Dynamically create the serializer class
    return type('{0}Serializer'.format(translated_model.__name__), (serializers.ModelSerializer,), attrs)
