# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http.response import HttpResponseForbidden, JsonResponse
from django.utils.translation import ugettext as _
from filer.models import Folder

from shuup.core.shop_provider import get_shop
from shuup.utils.filer import (
    ensure_media_file, ensure_media_folder, filer_file_to_json_dict,
    filer_image_from_upload
)


def file_size_validator(value):
    size = getattr(value, "size", None)
    if size and settings.SHUUP_FRONT_MAX_UPLOAD_SIZE and settings.SHUUP_FRONT_MAX_UPLOAD_SIZE < size:
        raise ValidationError(
            _("Maximum file size reached (%(size)s MB).") %
            {"size": settings.SHUUP_FRONT_MAX_UPLOAD_SIZE / 1000 / 1000},
            code="file_max_size_reached"
        )

    return value


class UploadImageForm(forms.Form):
    file = forms.ImageField(validators=[file_size_validator])


def get_or_create_folder(shop, path):
    folders = path.split("/")
    parent = None
    child = None
    created = False
    for folder in folders:
        if folder != "":
            child, created = Folder.objects.get_or_create(parent=parent, name=folder)
            ensure_media_folder(shop, child)
            parent = child
    return child


def media_upload(request, *args, **kwargs):
    if not settings.SHUUP_CUSTOMER_INFORMATION_ALLOW_PICTURE_UPLOAD:
        return HttpResponseForbidden()

    shop = get_shop(request)
    folder = get_or_create_folder(shop, "/contacts")
    form = UploadImageForm(request.POST, request.FILES)
    if form.is_valid():
        filer_file = filer_image_from_upload(request, path=folder, upload_data=request.FILES['file'])
    else:
        error_messages = []
        for validation_error in form.errors.as_data().get("file", []):
            error_messages += validation_error.messages

        return JsonResponse({"error": ", ".join([msg for msg in error_messages])}, status=400)

    ensure_media_file(shop, filer_file)
    return JsonResponse({"file": filer_file_to_json_dict(filer_file)})
