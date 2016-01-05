# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import copy
from collections import defaultdict

import six
from django.forms.models import model_to_dict, ModelForm
from django.utils.translation import get_language
from parler.forms import TranslatableModelForm

from shoop.utils.i18n import get_language_name


def to_language_codes(languages):
    languages = languages or (get_language(),)
    if languages and isinstance(languages[0], (list, tuple)):
        # `languages` looks like a `settings.LANGUAGES`, so fix it
        languages = [code for (code, name) in languages]
    return languages


class MultiLanguageModelForm(TranslatableModelForm):
    def _get_translation_model(self):
        return self._meta.model._parler_meta.root_model

    def __init__(self, **kwargs):
        self.languages = to_language_codes(kwargs.pop("languages", ()))

        self.default_language = kwargs.pop("default_language", getattr(self, 'language', get_language()))
        if self.default_language not in self.languages:
            raise ValueError("Language %r not in %r" % (self.default_language, self.languages))

        self.required_languages = kwargs.pop("required_languages", [self.default_language])

        opts = self._meta
        translations_model = self._get_translation_model()
        object_data = {}

        # We're not mutating the existing fields, so the shallow copy should be okay
        self.base_fields = self.base_fields.copy()
        self.translation_fields = [
            f for (f, _) in translations_model._meta.get_fields_with_model()
            if f.name not in ('language_code', 'master', 'id') and f.name in self.base_fields
        ]
        self.trans_field_map = defaultdict(dict)
        self.trans_name_map = defaultdict(dict)
        self.translated_field_names = []
        self.non_default_languages = sorted(set(self.languages) - set([self.default_language]))
        self.language_names = dict((lang, get_language_name(lang)) for lang in self.languages)

        for f in self.translation_fields:
            base = self.base_fields.pop(f.name, None)
            if not base:
                continue
            for lang in self.languages:
                language_field = copy.deepcopy(base)
                language_field_name = "%s__%s" % (f.name, lang)
                language_field.required = language_field.required and (lang in self.required_languages)
                language_field.label = "%s [%s]" % (language_field.label, self.language_names.get(lang))
                self.base_fields[language_field_name] = language_field
                self.trans_field_map[lang][language_field_name] = f
                self.trans_name_map[lang][f.name] = language_field_name
                self.translated_field_names.append(language_field_name)

        instance = kwargs.get("instance")
        initial = kwargs.get("initial")
        if instance is not None:
            assert isinstance(instance, self._meta.model)
            current_translations = dict(
                (trans.language_code, trans)
                for trans in translations_model.objects.filter(master=instance)
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

    def _save_translations(self, instance, data):
        translations_model = self._get_translation_model()
        current_translations = dict(
            (trans.language_code, trans)
            for trans
            in translations_model.objects.filter(master=instance, language_code__in=self.languages)
        )
        for lang, field_map in six.iteritems(self.trans_field_map):
            current_translations[lang] = translation = (
                current_translations.get(lang) or translations_model(master=instance, language_code=lang)
            )
            translation_fields = dict((src_name, data.get(src_name)) for src_name in field_map)
            for src_name, field in six.iteritems(field_map):
                field.save_form_data(translation, translation_fields[src_name])
            self._save_translation(instance, translation)

    def _save_translation(self, instance, translation):
        """
        Process saving a single translation.
        This could be used to delete unnecessary/cleared translations or skip
        saving translations altogether.

        :param instance: Parent model instance
        :type instance: django.db.models.Model
        :param translation: Translation model
        :type translation: parler.models.TranslatedFieldsModelBase
        """
        translation.save()

    def save(self, commit=True):
        self.instance.set_current_language(self.default_language)
        data = self.cleaned_data
        for field in self.translation_fields:
            field.save_form_data(self.instance, data["%s__%s" % (field.name, self.default_language)])

        self.pre_master_save(self.instance)
        instance = self.instance = super(ModelForm, self).save(True)  # We skip TranslatableModelForm on purpose!
        self._save_translations(instance, data)
        return self.instance

    def pre_master_save(self, instance):
        # Subclass hook
        pass
