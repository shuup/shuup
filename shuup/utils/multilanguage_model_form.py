# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import copy
import six
from collections import defaultdict
from django.conf import settings
from django.forms.models import ModelForm, model_to_dict
from django.utils.translation import get_language, ugettext_lazy as _
from parler.forms import TranslatableModelForm
from parler.utils.context import switch_language

from shuup.utils.i18n import get_language_name


def to_language_codes(languages, default_language):
    languages = languages or (get_language(),)
    if languages and isinstance(languages[0], (list, tuple)):
        # `languages` looks like a `settings.LANGUAGES`, so fix it
        languages = [code for (code, name) in languages]
    if default_language not in languages:
        raise ValueError("Error! Default language `%r` not in the list: `%r`." % (default_language, languages))
    languages = [default_language] + [code for code in languages if code != default_language]
    return languages


class MultiLanguageModelForm(TranslatableModelForm):
    def _get_translation_model(self):
        return self._meta.model._parler_meta.root_model

    def __init__(self, **kwargs):
        self.default_language = kwargs.pop(
            "default_language", getattr(self, "language", getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE"))
        )
        self.languages = to_language_codes(kwargs.pop("languages", ()), self.default_language)

        self.required_languages = kwargs.pop("required_languages", [self.default_language])

        opts = self._meta
        translations_model = self._get_translation_model()
        object_data = {}

        # We're not mutating the existing fields, so the shallow copy should be okay
        self.base_fields = self.base_fields.copy()
        self.translation_fields = [
            f
            for f in translations_model._meta.get_fields()
            if f.name not in ("language_code", "master", "id") and f.name in self.base_fields
        ]
        self.trans_field_map = defaultdict(dict)
        self.trans_name_map = defaultdict(dict)
        self.translated_field_names = []
        self.required_translated_field_names = []
        self.non_default_languages = sorted(set(self.languages) - set([self.default_language]))
        self.language_names = dict((lang, get_language_name(lang)) for lang in self.languages)

        for f in self.translation_fields:
            base = self.base_fields.pop(f.name, None)
            if not base:
                continue
            for lang in self.languages:
                language_field = copy.deepcopy(base)
                language_field_name = "%s__%s" % (f.name, lang)
                if language_field.required:
                    self.required_translated_field_names.append(language_field_name)
                language_field.required = language_field.required and (lang in self.required_languages)
                language_field.label = self._get_label(f.name, language_field, lang)
                self.base_fields[language_field_name] = language_field
                self.trans_field_map[lang][language_field_name] = f
                self.trans_name_map[lang][f.name] = language_field_name
                self.translated_field_names.append(language_field_name)

        instance = kwargs.get("instance")
        initial = kwargs.get("initial")
        if instance is not None:
            assert isinstance(instance, self._meta.model)
            current_translations = dict(
                (trans.language_code, trans) for trans in translations_model.objects.filter(master=instance)
            )
            object_data = {}
            for lang, trans in six.iteritems(current_translations):
                model_dict = model_to_dict(trans, opts.fields, opts.exclude)
                object_data.update(("%s__%s" % (fn, lang), f) for (fn, f) in six.iteritems(model_dict))

        if initial is not None:
            object_data.update(initial)
        kwargs["initial"] = object_data
        super(MultiLanguageModelForm, self).__init__(**kwargs)

    def __getitem__(self, key):
        try:
            return super(MultiLanguageModelForm, self).__getitem__(key)
        except KeyError:
            return super(MultiLanguageModelForm, self).__getitem__(key + "__" + self.default_language)

    def clean(self):
        """
        Avoid partially translated languages where the translated fields that
        are required are not set.
        """
        data = self.cleaned_data
        for language, field_names in self.trans_name_map.items():
            if not any(data.get(field_name) for field_name in field_names.values()):
                continue  # No need to check this language further
            for field_name in field_names.values():
                if field_name in self.required_translated_field_names and not data.get(field_name):
                    self.add_error(field_name, _("This field is required."))
        return data

    def _save_translations(self, instance, data):
        translations_model = self._get_translation_model()
        current_translations = dict(
            (trans.language_code, trans)
            for trans in translations_model.objects.filter(master_id=instance.id, language_code__in=self.languages)
        )
        for lang, field_map in six.iteritems(self.trans_field_map):
            translation_fields = dict((src_name, data.get(src_name)) for src_name in field_map)
            translation = current_translations.get(lang)
            # Add translation only if at least one translated field is given
            if not any(translation_fields.values()):
                if translation:
                    translation.delete()  # No translations set so delete the object also.
                continue
            current_translations[lang] = translation = translation or translations_model(
                master=instance, language_code=lang
            )
            for src_name, field in six.iteritems(field_map):
                field.save_form_data(translation, translation_fields[src_name])
            self._save_translation(instance, translation)

    def _save_translation(self, instance, translation):
        """
        Process saving a single translation.
        This could be used to delete unnecessary/cleared translations or skip
        saving translations altogether.

        :param instance: Parent model instance.
        :type instance: django.db.models.Model
        :param translation: Translation model.
        :type translation: parler.models.TranslatedFieldsModelBase
        """
        translation.save()

    def save(self, commit=True):
        self._set_fields_for_language(self.default_language)
        self.pre_master_save(self.instance)

        # Save is necessary here since translations can not be
        # attached to non-saved object
        self.instance = self._save_master(commit)
        self._save_translations(self.instance, self.cleaned_data)

        # Save the master once again since the save might involve
        # some procedures that requires translations like generating
        # slug from translated name.
        self._save_master(commit)
        return self.instance

    def _set_fields_for_language(self, language):
        with switch_language(self.instance, language):
            self.instance.set_current_language(language)
            for field in self.translation_fields:
                value = self.cleaned_data["%s__%s" % (field.name, language)]
                field.save_form_data(self.instance, value)

    def _save_master(self, commit=True):
        # We skip TranslatableModelForm on purpose!
        return super(ModelForm, self).save(True)

    def pre_master_save(self, instance):
        # Subclass hook
        pass

    def _get_cleaned_data_without_translations(self):
        """
        Get cleaned data without translated fields.
        """
        translated_field_names = set(self.translated_field_names)
        return dict((k, v) for (k, v) in six.iteritems(self.cleaned_data) if k not in translated_field_names)

    def _get_label(self, field_name, field, lang):
        label = field.label
        if self._meta.labels:
            label = self._meta.labels.get(field_name, field.label)
        if len(self.languages) > 1:
            return "%s [%s]" % (label, self.language_names.get(lang))
        return label
