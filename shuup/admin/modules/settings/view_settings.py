# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django
import six
from django.apps import apps
from django.conf import settings
from django.db.models import BooleanField, CharField, ForeignKey
from enumfields import EnumIntegerField

from shuup import configuration
from shuup.admin.utils.picotable import ChoicesFilter, Column, TextFilter, true_or_false_filter
from shuup.apps.provides import get_provide_objects
from shuup.utils.importing import load

INVALID_FIELDS = ["ptr", "ctype", "key", "label" "master"]


class ViewSettings(object):
    key = "view_configuration_%s_%s"
    column_spec = []

    def __init__(self, model, default_columns, view_context, *args, **kwargs):
        if isinstance(model, six.string_types) and model == settings.AUTH_USER_MODEL:
            model = apps.get_model(settings.AUTH_USER_MODEL)

        self.model = model
        self.default_columns = default_columns
        self.view_context = view_context
        self.ensure_initial_columns(default_columns)
        self.column_spec = self._build_settings_columns()
        self.active_columns = []
        self.inactive_columns = []
        self._create_columns()

    def _create_columns(self):
        for column in self.column_spec:
            config = self.get_config(column.id)
            try:
                # backwards compatibility
                int(config)
                old_mode = True
            except Exception:
                old_mode = False

            column.ordering = config.get("ordering", 9999) if not old_mode else 9999

            if old_mode:
                # old and active
                if config > 1:
                    self.active_columns.append(column)
                else:
                    self.inactive_columns.append(column)
            else:
                if config.get("active", False):
                    self.active_columns.append(column)
                else:
                    self.inactive_columns.append(column)

        self.active_columns.sort(key=lambda x: x.ordering)
        self.inactive_columns.sort(key=lambda x: x.title)
        self.columns = self.active_columns

    def ensure_initial_columns(self, default_columns):
        if not self.view_configured():
            # generate the default stuff
            for default_column in default_columns:
                self.set_config(default_column.id, {"ordering": default_column.ordering, "active": True})
            self.set_config("saved", True)

    def get_config(self, value):
        val = configuration.get(None, self.get_settings_key(value), {})
        return val

    def set_config(self, key_value, value, use_key=False):
        key = self.get_settings_key(key_value) if not use_key else key_value
        return configuration.set(None, key, value)

    def get_settings_key(self, value):
        return self.key % (self.model.__name__.lower(), value)

    def view_configured(self):
        return self.get_config("saved")

    def _valid_field(self, field_identifier):
        return not len([field for field in INVALID_FIELDS if field in field_identifier])

    def _build_settings_columns(self):
        columns = []
        all_models = [(None, self.model)]

        defaults = [col.id for col in self.default_columns]

        known_names = []

        for identifier, m in self.view_context.related_objects:
            all_models.append((identifier, load(m)))

        for identifier, model in all_models:
            if hasattr(model, "_parler_meta"):
                self._add_translated_columns(columns, defaults, identifier, known_names, model)
            self._add_local_columns(all_models, columns, defaults, identifier, known_names, model)
            self._add_m2m_columns(all_models, columns, defaults, identifier, known_names, model)
            self._add_provided_columns(columns, identifier, known_names, model)

        table_columns = set([col.id for col in columns])
        for default_column in self.default_columns:
            if default_column.id not in table_columns and default_column.id != "select":
                columns.append(default_column)
        return columns

    def _add_m2m_columns(self, all_models, columns, defaults, identifier, known_names, model):
        models_from_all_models = [model for identifier, model in all_models]
        for field in model._meta.local_many_to_many:
            if field.name in defaults:
                continue

            if django.VERSION < (1, 9):
                to = field.rel.to
            else:
                to = field.remote_field.target_field

            if to in models_from_all_models:
                continue  # no need to have these...

            column = self._get_column(model, field, known_names, identifier)
            if column:
                columns.append(column)

    def _add_local_columns(self, all_models, columns, defaults, identifier, known_names, model):
        models_from_all_models = [model for identifier, model in all_models]
        for field in model._meta.local_fields:
            if field.name in defaults:
                continue
            if field.name == "id" and model != self.model:
                continue

            if django.VERSION < (1, 9):
                if isinstance(field, ForeignKey) and field.rel.to in models_from_all_models:
                    continue  # no need to have these...
            else:
                if isinstance(field, ForeignKey) and field.remote_field.target_field in models_from_all_models:
                    continue  # no need to have these...

            column = self._get_column(model, field, known_names, identifier)
            if column:
                columns.append(column)

    def _add_translated_columns(self, columns, defaults, identifier, known_names, model):
        for field in model._parler_meta.root_model._meta.get_fields():
            if field.name in defaults:
                continue
            if field.name in ["id", "master", "language_code"]:  # exclude these fields
                continue
            column = self._get_translated_column(model, field, known_names, identifier)
            columns.append(column)

    def _get_translated_column(self, model, field, known_names, identifier):
        field_name = field.verbose_name.title()
        if identifier:
            field_name = "%s %s" % (identifier.replace("_", " ").capitalize(), field_name)

        # take the first extension, usually we should not have more then one
        translation_rel_name = model._parler_meta._extensions[0].rel_name

        if model != self.model:
            filter_field = "%s__%s__%s" % (identifier, translation_rel_name, field.name) if identifier else field.name
        else:
            filter_field = "%s__%s" % (translation_rel_name, field.name)

        display = "%s__%s" % (identifier, field.name) if identifier else field.name

        column = Column(
            "%s_%s" % ((identifier if identifier else model.__name__.lower()), field.name),
            field_name,
            sort_field=display,
            display=display,
            filter_config=TextFilter(filter_field=filter_field, placeholder=field_name),
        )
        return self.handle_special_column(field, column)[0]

    def handle_special_column(self, field, column):
        is_special = False
        for original_column in self.default_columns:
            if original_column.id == column.id:
                column.__dict__ = original_column.__dict__.copy()  # shallow copy
                is_special = True
        return (column, is_special)

    def _get_column(self, model, field, known_names, identifier):
        if not self._valid_field(field.name):
            return None

        field_name = field.verbose_name.title()
        if identifier:
            field_name = "%s %s" % (identifier.replace("_", " ").capitalize(), field_name)

        display = "%s__%s" % (identifier, field.name) if identifier else field.name

        column = Column(
            "%s_%s" % ((identifier if identifier else model.__name__.lower()), field.name), field_name, display=display
        )

        column, is_special = self.handle_special_column(field, column)
        if not is_special:
            if isinstance(field, CharField):
                column.filter_config = TextFilter(filter_field=field.name, placeholder=field_name)
            if isinstance(field, EnumIntegerField):
                column.filter_config = ChoicesFilter(field.choices)
            if isinstance(field, BooleanField):
                column.filter_config = true_or_false_filter
        return column

    def _add_provided_columns(self, columns, identifier, known_names, model):
        provide_object_key = "provided_columns_%s" % model.__name__
        for provided_column_object in get_provide_objects(provide_object_key):
            obj = provided_column_object()
            column = obj.get_column(model, known_names, identifier)
            if column:
                columns.append(column)
