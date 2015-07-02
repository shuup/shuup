# -*- coding: utf-8 -*-

"""Custom serializers suitable to translated models."""

from __future__ import absolute_import, unicode_literals
from rest_framework import serializers


class TranslatableModelSerializer(serializers.ModelSerializer):

    """Serializer that saves :class:`TranslatedFieldsField` automatically."""

    def save(self, **kwargs):
        """Extract the translations and save them after main object save.

        By default all translations will be saved no matter if creating
        or updating an object. Users with more complex needs might define
        their own save and handle translation saving themselves.
        """
        translated_data = self._pop_translated_data()
        instance = super(TranslatableModelSerializer, self).save(**kwargs)
        self.save_translations(instance, translated_data)
        return instance

    def _pop_translated_data(self):
        """Separate data of translated fields from other data."""
        translated_data = {}
        for meta in self.Meta.model._parler_meta:
            translations = self.validated_data.pop(meta.rel_name, {})
            if translations:
                translated_data[meta.rel_name] = translations
        return translated_data

    def save_translations(self, instance, translated_data):
        """Save translation data into translation objects."""
        for meta in self.Meta.model._parler_meta:
            translations = translated_data.get(meta.rel_name, {})
            for lang_code, model_fields in translations.items():
                translation = instance._get_translated_model(lang_code, auto_create=True, meta=meta)
                for field, value in model_fields.items():
                    setattr(translation, field, value)
                translation.save()
