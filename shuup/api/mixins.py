# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.response import Response


class PermissionHelperMixin(object):
    """
    Mixin to return a helper text to admin users in permission configuration.
    """
    @classmethod
    def get_help_text(cls):
        raise NotImplementedError()


class ProtectedModelViewSetMixin(object):
    """
    Mixin to catch ProtectedError exceptions and return a reasonable response error to the user.
    """

    def destroy(self, request, *args, **kwargs):
        try:
            return super(ProtectedModelViewSetMixin, self).destroy(request, *args, **kwargs)
        except ProtectedError as exc:
            ref_obj = exc.protected_objects[0].__class__.__name__
            msg = "This object can not be deleted because it is referenced by {}".format(ref_obj)
            return Response(data={"error": msg}, status=status.HTTP_400_BAD_REQUEST)


class SearchableMixin(object):
    """
    Mixin to give search capabilities for `ViewSet`
    """
    filter_backends = (SearchFilter,)
    search_fields = ("=id",)
