# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import logging
import os
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum

from shuup.admin.utils.permissions import has_permission
from shuup.apps.provides import get_provide_objects
from shuup.importer.exceptions import ImporterError
from shuup.importer.transforms import transform_file

LOGGER = logging.getLogger(__name__)


class ImportMode(Enum):
    CREATE_UPDATE = "create,update"
    CREATE = "create"
    UPDATE = "update"

    class Labels:
        CREATE_UPDATE = _("Allow create and update")
        CREATE = _("Only create (no updates)")
        UPDATE = _("Only update existing (no new ones are created)")


def get_importer_choices(user=None):
    # filter the importers by the user
    if user:
        return [
            (importer.identifier, importer.name)
            for importer in get_provide_objects("importers")
            if has_permission(user, importer.get_permission_identifier())
        ]

    return [(i.identifier, i.name) for i in get_provide_objects("importers")]


def get_importer(identifier):
    for i in get_provide_objects("importers"):
        if i.identifier == identifier:
            return i
    return None


def get_import_file_path(filename):
    return os.path.join(settings.MEDIA_ROOT, "import_temp", os.path.basename(filename))


class FileImporter:
    def __init__(
        self,
        importer: str,
        import_mode: ImportMode,
        file_name: str,
        language: str = None,
        mapping={},
        shop=None,
        supplier=None,
        user=None,
        **kwargs
    ):
        self.importer = None
        self.importer_cls = get_importer(importer)
        self.import_mode = import_mode
        self.file_name = file_name
        self.language = language
        self.shop = shop
        self.supplier = supplier
        self.mapping = mapping
        self.user = user

    def prepare(self):
        self.data = self._transform_request_file()

        if self.data is None:
            raise ImporterError(_("The file doesn't contain data."))

        context = self.importer_cls.get_importer_context(
            request=None, shop=self.shop, language=self.language, supplier=self.supplier, user=self.user
        )
        self.importer = self.importer_cls(self.data, context)
        self.importer.process_data()

        # check if mapping was done
        if self.mapping:
            for field in self.importer.unmatched_fields:
                values = self.mapping.get(field)
                if len(values):
                    self.importer.manually_match(field, values[0])

                self.importer.do_remap()

        return True

    def import_file(self):
        if self.data is None:
            raise ImporterError(_("The file doesn't contain data."))

        try:
            self.importer.do_import(self.import_mode)
        except Exception as exc:
            LOGGER.exception("Failed to run importer.")
            raise ImporterError(_("Failed to import data: {}.").format(str(exc)))

    def _transform_request_file(self):
        try:
            filename = get_import_file_path(self.file_name)
            if not os.path.isfile(filename):
                raise ImporterError(_("{file_name} is not a valid file.").format(file_name=self.file_name))
        except Exception:
            raise ImporterError(_("The file is missing."))
        try:
            mode = "xls"
            if filename.endswith("xlsx"):
                mode = "xlsx"
            if filename.endswith("csv"):
                mode = "csv"

            if self.importer_cls.custom_file_transformer:
                return self.importer_cls.transform_file(mode, filename)

            return transform_file(mode, filename)

        except (Exception, RuntimeError) as e:
            raise ImporterError(str(e))
