# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import logging
from django.contrib.auth import get_user_model
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _
from typing import TYPE_CHECKING

from shuup.core.models import Shop, Supplier
from shuup.core.tasks import TaskResult
from shuup.importer.exceptions import ImporterError
from shuup.importer.utils.importer import FileImporter, ImportMode

if TYPE_CHECKING:  # pragma: no cover
    from shuup.importer.importing import DataImporter

LOGGER = logging.getLogger(__name__)


def import_file(importer, import_mode, file_name, language, shop_id, supplier_id=None, user_id=None, mapping=None):
    shop = Shop.objects.get(pk=shop_id)
    supplier = None
    user = None

    if supplier_id:
        supplier = Supplier.objects.filter(pk=supplier_id).first()

    if user_id:
        user = get_user_model().objects.get(pk=user_id)

    # convert to enum
    import_mode = ImportMode(import_mode)

    file_importer = FileImporter(
        importer, import_mode, file_name, language, mapping=mapping, shop=shop, supplier=supplier, user=user
    )

    try:
        file_importer.prepare()

        with atomic():
            file_importer.import_file()

            importer_instance = file_importer.importer  # type: DataImporter
            result = dict(
                other_log_messages=[str(msg) for msg in importer_instance.other_log_messages],
                log_messages=[str(msg) for msg in importer_instance.log_messages],
            )

            new_objects = []
            updated_objects = []

            for new_object in importer_instance.new_objects:
                new_objects.append(
                    {"model": f"{new_object._meta.app_label}.{new_object._meta.model_name}", "pk": new_object.pk}
                )
            for updated_object in importer_instance.updated_objects:
                updated_objects.append(
                    {
                        "model": f"{updated_object._meta.app_label}.{updated_object._meta.model_name}",
                        "pk": updated_object.pk,
                    }
                )

            result["new_objects"] = new_objects
            result["updated_objects"] = updated_objects

            return TaskResult(result=result)

    except ImporterError as error:
        error_log = ", ".join(error.messages)
        return TaskResult(error_log=error_log)

    except Exception:
        LOGGER.exception("Failed to import the file.")
        return TaskResult(error_log=_("Unexpected error while trying to import the file."))
