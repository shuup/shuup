# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import datetime
import itertools
import logging
from operator import iand, ior

import django
import six
import xlrd
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import AutoField, ForeignKey, Q
from django.db.models.fields import BooleanField
from django.db.models.fields.related import RelatedField
from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumIntegerField

from shuup.importer._mapper import RelatedMapper
from shuup.importer.exceptions import ImporterError
from shuup.importer.importing.meta import ImportMetaBase
from shuup.importer.importing.session import DataImporterRowSession
from shuup.importer.utils import copy_update, fold_mapping_name
from shuup.importer.utils.importer import ImportMode
from shuup.utils.django_compat import force_text

LOGGER = logging.getLogger(__name__)


class ImporterExampleFile(object):
    file_name = ""
    template_name = ""
    content_type = ""

    def __init__(self, file_name, content_type, template_name=None):
        self.file_name = file_name
        self.content_type = content_type
        self.template_name = template_name


class ImporterContext:
    shop = None  # shuup.core.models.Shop
    language = None  # str

    def __init__(self, shop, language, **kwargs):
        """
        :type shop: shuup.core.models.Shop
        :param shop: the current shop

        :type language: shuup.core.models.Shop
        :param language: the current shop

        """
        self.shop = shop
        self.language = language


class DataImporter(object):
    identifier = None
    name = None
    meta_class_getter_name = "get_import_meta"
    meta_base_class = ImportMetaBase
    extra_matches = {}
    custom_file_transformer = False

    unique_fields = {}
    unmatched_fields = set()
    relation_map_cache = {}

    example_files = []  # list[ImporterExampleFile]
    help_template = None

    model = None

    @classmethod
    def get_importer_context(cls, request, **defaults):
        """
        Returns a context object for the given `request`
        that will be used on the importer process.

        :type request: django.http.HttpRequest
        :type defaults: dict

        :rtype: ImporterContext
        """
        return ImporterContext(**defaults)

    def __init__(self, data, context):
        """
        :type context: ImporterContext
        """
        self.data = data
        self.data_keys = data[0].keys()

        self.shop = context.shop
        self.language = context.language
        self.context = context

        meta_class_getter = getattr(self.model, self.meta_class_getter_name, None)
        meta_class = meta_class_getter() if meta_class_getter else self.meta_base_class
        self._meta = (meta_class(self, self.model) if meta_class else None)

        self.field_defaults = self._meta.get_import_defaults()

        self.other_log_messages = []
        self.new_objects = []
        self.updated_objects = []
        self.log_messages = []

    @classmethod
    def get_permission_identifier(cls):
        return "{}:{}".format(cls.identifier, force_text(cls.name))

    @classmethod
    def transform_file(cls, mode, filename, data=None):
        """
        That method will be called if `cls.custom_file_transformer` is True
        """
        raise NotImplementedError(
            "Error! Not implemented: `DataImporter` -> `transform_file()`. "
            "Implement `transform_file()` function or set `custom_file_transformer` to False")

    def process_data(self):
        mapping = self.create_mapping()
        data_map = self.map_data_to_fields(mapping)
        return data_map

    def create_mapping(self):
        mapping = {}
        aliases = self._meta.field_aliases
        for model in self.get_related_models():
            for field, mode in self._get_fields_with_modes(model):
                map_base = self._get_map_base(field, mode)

                if isinstance(field, RelatedField) and not field.null:
                    map_base["priority"] -= 10

                # Figure out names
                names = [field.name]
                if field.verbose_name:
                    names.append(field.verbose_name)

                # find aliases
                this_aliases = aliases.get(field.name)
                if this_aliases:
                    if isinstance(this_aliases, six.string_types):
                        this_aliases = [this_aliases]
                    names.extend(this_aliases)

                # Assign into mapping
                for name in names:
                    if name in self._meta.fields_to_skip:
                        continue

                    if map_base.get("translated"):
                        mapping[name] = copy_update(map_base, lang=self.language)
                    else:
                        mapping[name] = map_base

        mapping = dict((fold_mapping_name(mname), mdata) for (mname, mdata) in six.iteritems(mapping))
        self.mapping = mapping
        return mapping

    def map_data_to_fields(self, model_mapping):
        """
        Map fields.

        If field is not found it will be saved into unmapped
        :return:
        """
        # reset unmatched here
        self.unmatched_fields = set()

        data_map = {}
        for field_name in sorted(self.data_keys):
            mfname = fold_mapping_name(field_name)

            if mfname == "ignore" or mfname in self._meta.fields_to_skip:
                continue

            mapped_value = model_mapping.get(mfname)
            if not mapped_value:
                for fld, opt in six.iteritems(model_mapping):
                    matcher = opt.get("matcher")
                    if matcher and (matcher(field_name) or matcher(mfname)):
                        mapped_value = opt
                        break

            if mapped_value:
                data_map[field_name] = mapped_value
                if mapped_value.get("keyable"):
                    self.unique_fields[field_name] = mapped_value

            elif not mapped_value and not self._meta.has_post_save_handler(field_name):
                self.unmatched_fields.add(field_name)

        self.data_map = data_map
        return data_map

    def manually_match(self, imported_field_name, target_field_name):
        if target_field_name == "0":  # nothing was selected
            return

        target_model, shuup_field_name = target_field_name.split(":")
        mapping = self.mapping.get(shuup_field_name)

        mapping["matcher"] = self.matcher
        mapping["setter"] = self.set_extra_match

        self.extra_matches[target_field_name] = imported_field_name
        self.mapping[shuup_field_name] = mapping
        return self.mapping

    def do_remap(self):
        self.map_data_to_fields(self.mapping)

    def matcher(self, value):
        for original_field, new_field in six.iteritems(self.extra_matches):
            if new_field == value:
                return True
        return False

    def set_extra_match(self, sess, value, mapping):
        target_field = mapping.get("id")
        if target_field:
            setattr(sess.instance, target_field, value)

    def do_import(self, import_mode):
        self.import_mode = import_mode

        self.other_log_messages = []
        self.new_objects = []
        self.updated_objects = []
        self.log_messages = []

        for row in self.data:
            self.process_row(row)

    def resolve_object(self, cls, value):
        try:
            value = int(value)
            return cls.objects.get(pk=value)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            name_fields = ["name", "title"]
            query = Q()

            for field in name_fields:
                if hasattr(cls, "_parler_meta") and field in cls._parler_meta.get_translated_fields():
                    field = "%s__%s" % (cls._parler_meta.root_rel_name, field)
                else:
                    from django.core.exceptions import FieldDoesNotExist
                    try:
                        cls._meta.get_field(field)
                    except FieldDoesNotExist:
                        continue

                query |= Q(**{field: value})

            if query:
                return cls.objects.get(query)

    def _resolve_obj(self, row):
        obj = self._find_matching_object(row, self.shop)
        if not obj:
            if self.import_mode == ImportMode.UPDATE:
                self.other_log_messages.append(_("Row ignored (no existing item and creating new is not allowed)."))
                return (None, True)

            self.target_model = self.find_matching_model(row)
            obj = self.target_model(**self.field_defaults)
            new = True
        else:
            new = False
            if self.import_mode == ImportMode.CREATE:
                self.other_log_messages.append(
                    _("Row ignored (object already exists (%(object_name)s with id: %(object_id)s).") % {
                        "object_name": str(obj),
                        "object_id": obj.pk
                    }
                )
                return (None, False)

        if hasattr(obj, "_parler_meta"):
            obj.set_current_language(self.language)

        return (obj, new)

    def _row_valid(self, mapping, value, obj):
        if not mapping.get("writable"):
            return False
        if obj.pk and value is None:  # Don't empty fields
            return False
        return True

    @atomic  # noqa (C901)
    def process_row(self, row):
        if all((not val) for val in row.values()):  # Empty row, skip it
            return

        # ignore the row if there is a column 'ignore" with a valid value
        row_lower = {key.lower(): val for key, val in row.items()}
        if row_lower.get("ignore"):
            return

        row = self._meta.pre_process_row(row)

        if self._meta.should_skip_row(row):
            return

        obj, new = self._resolve_obj(row)
        if not obj:
            return

        row_session = DataImporterRowSession(self, row, obj, self.shop)
        for fname, mapping in sorted(six.iteritems(self.data_map), key=lambda x: (x[1].get("priority"), x[0])):
            field = mapping.get("field")
            if not field:
                continue

            if field.name in self._meta.fields_to_skip:
                continue
            value = orig_value = row.get(fname)
            if not self._row_valid(mapping, value, obj):
                continue

            value = self._handle_special_row_values(mapping, value)
            setter = mapping.get("setter")
            if setter:
                value, has_related = self._handle_related_value(field, mapping, orig_value, row_session, obj, value)
                setter(row_session, value, mapping)
                continue

            value, has_related = self._handle_related_value(field, mapping, orig_value, row_session, obj, value)
            if has_related:
                continue

            if field and not field.blank and value in (None, ""):
                continue  # Skip fields that require a value but don't have one in the original data.

            self._handle_row_field(field, mapping, orig_value, row_session, obj, value)

        self.save_row(new, row_session)

    def _handle_related_value(self, field, mapping, orig_value, row_session, obj, value):
        has_related = False
        if mapping.get("fk"):
            value = self._handle_row_fk_value(field, orig_value, row_session, value)
            if not field.null and value is None:
                has_related = True
        elif mapping.get("m2m"):
            self._handle_row_m2m_value(field, orig_value, row_session, obj, value)
            has_related = True
        elif mapping.get("is_enum_field"):
            for k, v in field.get_choices():
                if fold_mapping_name(force_text(v)) == fold_mapping_name(orig_value):
                    value = k
                    break
        return (value, has_related)

    def _handle_special_row_values(self, mapping, value):
        if mapping.get("datatype") in ["datetime", "date"]:
            if isinstance(value, float):  # Sort of terrible
                value = datetime.datetime(*xlrd.xldate_as_tuple(value, self.data.meta["xls_datemode"]))
        if isinstance(value, float):
            if int(value) == value:
                value = int(value)
        return value

    def _handle_row_field(self, field, mapping, orig_value, row_session, target, value):
        value = self._get_field_choices_value(field, value)

        if isinstance(field, BooleanField):
            if not value or value == "" or value == " ":
                value = False

        if mapping.get("fk") and value is not None and value.pk:
            setattr(target, field.name, value)
        else:
            try:
                value = field.to_python(value)
            except Exception as exc:
                LOGGER.exception("Failed to convert field")

                row_session.log(
                    _("Failed while setting value for field %(field_name)s. (%(exception)s)") % {
                        "field_name": (field.verbose_name or field.name),
                        "exception": exc
                    }
                )
            else:
                value = self._meta.mutate_normal_field_set(row_session, field, value, original=orig_value)
            setattr(target, field.name, value)

    def _get_field_choices_value(self, field, value):
        if field.choices:
            for (ck, cv) in field.choices:
                if value in (ck, cv):
                    value = ck
                    break
        return value

    def _handle_row_m2m_value(self, field, orig_value, row_session, target, value):
        value = self.process_related_value(row_session, field, value, multi=True)
        if orig_value and not value:
            row_session.log(
                _("Couldn't set value %(original_value)s for field %(field_name)s.") % {
                    "original_value": orig_value,
                    "field_name": (field.verbose_name or field.name)
                }
            )

        row_session.defer("m2m_%s" % field.name, target, {field.name: value})

    def _handle_row_fk_value(self, field, orig_value, row_session, value):
        value = self.process_related_value(row_session, field, value, multi=False)
        if orig_value and not value:
            row_session.log(
                _("Couldn't set value %(original_value)s for field %(field_name)s.") % {
                    "original_value": orig_value,
                    "field_name": (field.verbose_name or field.name)
                }
            )
        return value

    def save_row(self, new, row_session):
        self._meta.presave_hook(row_session)
        try:
            row_session.save()
            self._meta.postsave_hook(row_session)
            (self.new_objects if new else self.updated_objects).append(row_session.instance)

            for post_save_handler, fields in six.iteritems(self._meta.post_save_handlers):
                if hasattr(self._meta, post_save_handler):
                    func = getattr(self._meta, post_save_handler)
                    func(fields, row_session)

            if row_session.log_messages:
                self.log_messages.append({
                    "instance": row_session.instance,
                    "messages": row_session.log_messages
                })
        except ImporterError as e:
            LOGGER.exception(e.message)
            self.other_log_messages.append(e.message)

    def get_fields_for_mapping(self, only_non_mapped=True):
        """
        Get fields for manual mapping.

        :return: List of fields `module_name.Model:field` or empty list
        :rtype: list
        """
        fields = []
        mapped_keys = [k for k in self.data_map]
        for model in self.get_related_models():
            for field in model._meta.local_fields:
                if only_non_mapped and field.name in mapped_keys:
                    continue
                model_field = "%s:%s" % (model.__name__, field.name)
                fields.append((model_field, field.verbose_name))
            if hasattr(model, "_parler_meta"):
                for field in model._parler_meta.root_model._meta.get_fields():
                    if only_non_mapped and field.name in mapped_keys:
                        continue
                    model_field = "%s:%s" % (model.__name__, field.name)
                    fields.append((model_field, field.verbose_name))
        return fields

    def _get_map_base(self, field, mode):
        is_translation = (mode == 2)
        is_m2m = (mode == 1)
        is_fk = isinstance(field, ForeignKey)
        is_enum_field = isinstance(field, EnumIntegerField)
        return {
            "name": field.verbose_name or field.name,
            "id": field.name,
            "field": field,
            "keyable": field.unique,
            "writable": field.editable and not isinstance(field, AutoField),
            "pk": bool(field.primary_key),
            "translated": is_translation,
            "priority": 0,
            "m2m": is_m2m,
            "fk": is_fk,
            "is_enum_field": is_enum_field,
        }

    def _find_matching_object(self, row, shop):
        """
        Find object that matches the given row and shop.

        :return: Found object or ``None``
        """
        field_map_values = [(fname, mapping, row.get(fname)) for (fname, mapping) in six.iteritems(self.unique_fields)]
        row_keys = dict((mapping["field"].name, value) for (fname, mapping, value) in field_map_values if value)
        if row_keys:
            qs = [Q(**{fname: value}) for (fname, value) in six.iteritems(row_keys)]
            fields = [field.name for field in self.model._meta.local_fields]
            if "shop" in fields:
                qs &= Q(shop=shop)
            if "shops" in fields:
                qs &= Q(shops=shop)

            and_query = six.moves.reduce(iand, [Q()] + qs)
            or_query = six.moves.reduce(ior, [Q()] + qs)

            try:
                return self.model.objects.get(and_query)
            except (ObjectDoesNotExist, MultipleObjectsReturned):  # Found multiple or zero -- not okay
                pass

            return self.model.objects.filter(or_query).first()
        return None

    def _get_fields_with_modes(self, model):

        return itertools.chain(
            zip(model._meta.local_fields, itertools.repeat(0)),
            zip(model._meta.local_many_to_many, itertools.repeat(1)),
            zip((f for f in model._parler_meta.root_model._meta.get_fields()
                 if f.name not in ("id", "master", "language_code")), itertools.repeat(2))
            if hasattr(model, "_parler_meta") else ()
        )

    def get_related_models(self):
        return [self.model]

    def get_row_model(self, row):
        """
        Get model that matches the row.

        Can be used in cases where you have multiple types of data in same import.

        :param row: A row dict.
        """
        return self.model

    def can_create_object(self, obj):
        """
        Returns whether the importer can create the given object.
        This is useful to handle related objects creation and
        skip them when needed.
        """
        return True

    @property
    def is_multi_model(self):
        return (len(self.get_related_models()) > 1)

    def find_matching_model(self, row):
        if not self.is_multi_model:
            return self.model
        return self.get_row_model(row)

    def process_related_value(self, row_session, field, value, multi, reverse=False):
        """
        Process Related values.

        :param field: Django Field object.
        :return: Found value
        """
        if django.VERSION < (1, 9):
            to = field.rel.to
        else:
            to = field.remote_field.target_field

        mapper = self.relation_map_cache.get(to)

        if not mapper:
            self.relation_map_cache[field] = mapper = RelatedMapper(handler=self, row_session=row_session, field=field)
        if reverse:
            if multi:
                return mapper.map_instances(value)
            return mapper.map_instance(value)
        else:
            if multi:
                return mapper.map_multi_value(value)
            return mapper.map_single_value(value)

    @classmethod
    def get_help_context_data(cls, request):
        """
        Returns the context data that should be used for help texts in admin.
        """
        return {}

    @classmethod
    def has_example_file(cls):
        return len(cls.example_files)

    @classmethod
    def get_example_file(cls, file_name):
        """
        :param file_name str
        :rtype ImporterExampleFile
        """
        for example_file in cls.example_files:
            if example_file.file_name == file_name:
                return example_file

    @classmethod
    def get_example_file_content(cls, example_file, request):
        """
        Returns a binary file that will be served through the request.
        This base implementation just renders a template and returns the result as BytesIO or StringIO.
        Override this method to return a custom file content.

        :param request HttpRequest
        :rtype StringIO|BytesIO
        """
        if example_file.template_name:
            from django.template import loader
            from six import StringIO
            file_content = StringIO()
            file_content.write(loader.render_to_string(
                template_name=example_file.template_name,
                context={},
                request=request)
            )
            return file_content
