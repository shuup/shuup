# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import unicodecsv as csv
from django.db.models import Q
from django.http import HttpResponse
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

from shuup.admin.modules.settings.view_settings import ViewSettings
from shuup.admin.utils.picotable import PicotableFileMassAction


class BaseExportCSVMassAction(PicotableFileMassAction):
    label = _("Export as CSV file")
    model = None
    filename = None
    view_class = None

    def get_queryset(self, request, view, ids):
        query = Q()
        if ids != "all":
            query = Q(pk__in=ids)
        return view.get_queryset().filter(query)

    def process(self, request, ids):
        view_instance = self.view_class()
        view_instance.request = request
        view_settings = ViewSettings(self.model, self.view_class.default_columns, view_instance)
        queryset = self.get_queryset(request, view_instance, ids)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}"'
        writer = csv.writer(response, delimiter=";", encoding="utf-8")
        writer.writerow([col.title for col in view_settings.columns])

        for item in queryset:
            row = []
            for dr in view_settings.columns:
                if dr.get_display_value(view_settings.view_context, item):
                    row.append(strip_tags(dr.get_display_value(view_settings.view_context, item)))
                else:
                    row.append(None)
            writer.writerow(row)

        return response
