# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import logging
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _

from shuup.core.models import Shop, Supplier
from shuup.core.tasks import TaskResult
from shuup.importer.exceptions import ImporterError
from shuup.importer.utils.importer import FileImporter

LOGGER = logging.getLogger(__name__)


def import_file(importer, import_mode, file_name, language, shop_id, supplier_id=None, mapping=None):
    shop = Shop.objects.get(pk=shop_id)
    supplier = None

    if supplier_id:
        supplier = Supplier.objects.filter(pk=supplier_id).first()

    file_importer = FileImporter(
        importer, import_mode, file_name, language, mapping=mapping, shop=shop, supplier=supplier
    )

    try:
        file_importer.prepare()

        with atomic():
            file_importer.import_file()
            result = dict()
            return TaskResult(result=result)

    except ImporterError as error:
        error_log = ", ".join(error.messages)
        return TaskResult(error_log=error_log)

    except Exception:
        LOGGER.exception("Failed to import the file.")
        return TaskResult(error_log=_("Unexpected error while trying to import the file."))
