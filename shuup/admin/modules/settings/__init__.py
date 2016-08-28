# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.apps import apps
from django.conf import settings
from django.db.models import BooleanField, CharField
from enumfields import EnumIntegerField

from shuup import configuration
from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, TextFilter, true_or_false_filter
)

INVALID_FIELDS = [
    "ptr",
    "ctype",
    "key",
    "label"
    "master"
]


class ViewSettings(object):
    key = "view_configuration_%s_%s"
    column_spec = []

    def __init__(self, model, default_columns, *args, **kwargs):
        if isinstance(model, six.string_types) and model == settings.AUTH_USER_MODEL:
            model = apps.get_model(settings.AUTH_USER_MODEL)

        self.model = model
        self.default_columns = default_columns
        self.ensure_initial_columns(default_columns)
        self.column_spec = self._build_settings_columns()
        self.columns = [column for column in self.column_spec if self.get_config(column.id)]

    def ensure_initial_columns(self, default_columns):
        if not self.view_configured():
            # generate the default stuff
            for default_column in default_columns:
                self.set_config(default_column.id, 1)
            self.set_config("saved", True)

    def get_config(self, value):
        val = configuration.get(None, self.get_settings_key(value), None)
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

        if hasattr(self.model, "_parler_meta"):
            for field in self.model._parler_meta.root_model._meta.get_fields():
                if field.name == "id":  # we don't want duplicate id's
                    continue
                column = self._get_translated_column(field)
                columns.append(column)

        for field in self.model._meta.local_fields:
            column = self._get_column(field)
            if column:
                columns.append(column)

        return columns

    def _get_translated_column(self, field):
        field_name = field.verbose_name.title()
        filter_config = TextFilter(
            filter_field="translations__%s" % field.name,
            placeholder=field_name
        )
        column = Column(
            field.name,
            field_name,
            sort_field="translations__%s" % field.name,
            display=field.name,
            filter_config=filter_config
        )
        return self.handle_special_column(field, column)[0]

    def handle_special_column(self, field, column):
        is_special = False
        for original_column in self.default_columns:
            if original_column.id == column.id:
                column.__dict__ = original_column.__dict__.copy()  # shallow copy
                is_special = True
        return (column, is_special)

    def _get_column(self, field):
        field_name = field.verbose_name.title()
        if not self._valid_field(field.name):
            return None
        column = Column(field.name, field_name, display=field.name)
        column, is_special = self.handle_special_column(field, column)
        if not is_special:
            if isinstance(field, CharField):
                column.filter_config = TextFilter(placeholder=field_name)
            if isinstance(field, EnumIntegerField):
                column.filter_config = ChoicesFilter(field.choices)
            if isinstance(field, BooleanField):
                column.filter_config = true_or_false_filter
        return column
