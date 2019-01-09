# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.dateparse import parse_datetime
from rest_framework import filters


class ModifiedAfterDateFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        modified_date_param = getattr(view, "modified_date_param", "modified_after")
        modified_date_field = getattr(view, "modified_date_field", "modified_on")

        if request.query_params.get(modified_date_param):
            modified_date = parse_datetime(request.query_params[modified_date_param])
            if modified_date:
                queryset = queryset.filter(**{"{}__gt".format(modified_date_field): modified_date})

        return queryset
