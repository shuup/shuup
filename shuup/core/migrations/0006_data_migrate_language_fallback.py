# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import apps as django_apps
from django.conf import settings
from django.db import migrations
from django.utils import translation
from parler.models import TranslatableModel, TranslationDoesNotExist
from django.db.utils import OperationalError


def to_language_codes(languages):
    languages = languages or (translation.get_language(),)
    if languages and isinstance(languages[0], (list, tuple)):
        # `languages` looks like a `settings.LANGUAGES`, so fix it
        languages = [code for (code, name) in languages]
    return languages


def save_values_from_default_to_lang(default_translation, translation_object, fields):

    for field in fields:
        default_value = getattr(default_translation, field.name, '')
        orig_value = getattr(translation_object, field.name)

        if not orig_value and default_value != orig_value:
            setattr(translation_object, field.name, default_value)

        translation_object.save()


def add_missing_values(model, default_lang, languages):

    objects = model.objects.all()

    _translations = getattr(model, 'translations', getattr(model, 'base_translations', None))

    translation_model = _translations.related.related_model

    base_fields = translation_model.get_translated_fields()

    translation_model_fields = [
        f for f in translation_model._meta.fields
        if f.name in base_fields and not f.unique
    ]

    try:
        for obj in objects:
            # model being translatable does not guarantee translations exist
            if _translations.count():
                default_translation = obj.get_translation(default_lang)

                for lang in languages:
                    if lang == default_lang:
                        continue
                    try:
                        save_values_from_default_to_lang(
                            default_translation, obj.get_translation(lang), translation_model_fields)
                    except TranslationDoesNotExist:
                        # translation for lang does not exist so skip it.
                        pass
    except OperationalError:
        # Ignores cases where model's' table doesn't exist yet. This may happen if
        # migration runs on empty DB and not all models tables have been created yet.
        pass


def fallback_language_migration(apps, schema_editor):

    translatable_models = [model for model in django_apps.get_models()
                           if issubclass(model, TranslatableModel)]

    default_lang = settings.PARLER_DEFAULT_LANGUAGE_CODE
    languages = to_language_codes(settings.LANGUAGES)

    for model in translatable_models:
        add_missing_values(model, default_lang, languages)


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
         migrations.RunPython(fallback_language_migration, reverse_code=migrations.RunPython.noop),
    ]
