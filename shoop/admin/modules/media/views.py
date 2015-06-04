# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import json

from django.conf import settings
from django.core.files.uploadedfile import TemporaryUploadedFile, InMemoryUploadedFile
from django.http.response import JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from filer.models import Folder, File
from mptt.templatetags.mptt_tags import cache_tree_children
from shoop.utils.filer import filer_file_from_upload, filer_image_from_upload
from six import BytesIO


def _filer_file_to_json_dict(file):
    """
    :type file: filer.models.File
    :rtype: dict
    """
    try:
        thumbnail = file.easy_thumbnails_thumbnailer.get_thumbnail({
            'size': (128, 128),
            'crop': True,
            'upscale': True,
            'subject_location': file.subject_location
        })
    except Exception:
        thumbnail = None
    return {
        "id": file.id,
        "name": file.label,
        "size": file.size,
        "url": file.url,
        "thumbnail": (thumbnail.url if thumbnail else None),
        "date": file.uploaded_at.isoformat()
    }


def _filer_folder_to_json_dict(folder, children=None):
    """
    :type file: filer.models.Folder
    :rtype: dict
    """
    if folder and children is None:
        # This allows us to pass `None` as a pseudo root folder
        children = folder.get_children()
    return {
        "id": folder.pk if folder else 0,
        "name": folder.name if folder else "Root",
        "children": [_filer_folder_to_json_dict(child) for child in children]
    }


def handle_filedrop_upload(request):
    """
    Squeeze out an UploadedFile from a request sent through FileDrop.js.

    FileDrop.js's AJAX mode passes the actual file data
    as an unembellished binary stream as the POST payload
    so we need to do some magic that normal (multipart/form-data)
    uploads would not require.

    Here's that magic.

    :param request: HTTP request.
    :type request: django.http.HttpRequest
    :return: Uploaded file.
    :rtype: django.core.files.uploadedfile.UploadedFile
    """

    content_type = request.META.get("HTTP_X_FILE_TYPE", "")
    filename = request.META["HTTP_X_FILE_NAME"]
    size = int(request.META["HTTP_X_FILE_SIZE"])

    if size >= settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
        upload_file = TemporaryUploadedFile(
            name=filename, content_type=content_type, size=size, charset="binary"
        )
    else:
        upload_file = InMemoryUploadedFile(
            name=filename, content_type=content_type, size=size, charset="binary", field_name="none", file=BytesIO()
        )

    upload_file.write(request.read())
    return upload_file


class MediaBrowserView(TemplateView):
    """
    A view for browsing media.

    Most of this is just a JSON API that the Javascript (`static_src/media/browser`) uses.
    """
    template_name = "shoop/admin/media/browser.jinja"
    title = _(u"Browse Media")

    def get(self, request, *args, **kwargs):
        action = request.REQUEST.get("action")
        if action == "folders":
            return self.handle_get_folders(request.REQUEST)
        if action == "folder":
            return self.handle_folder(request.REQUEST)

        return super(MediaBrowserView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.REQUEST.get("action") == "upload":
            return self.handle_upload()

        # Instead of normal POST variables, the Mithril `m.request()`
        # method passes data as a JSON payload (which is a good idea,
        # as it allows shedding the legacy of form data), so we need
        # to parse that.

        data = json.loads(request.body.decode("utf-8"))
        action = data.get("action")
        if action == "new_folder":
            return self.handle_new_folder(data)
        return JsonResponse({"error": "unknown action %s" % action})

    def handle_get_folders(self, data):
        root_folders = cache_tree_children(Folder.objects.all())
        return JsonResponse({"rootFolder": _filer_folder_to_json_dict(None, root_folders)})

    def handle_new_folder(self, data):
        parent_id = int(data["parent"])
        if parent_id > 0:
            parent = Folder.objects.get(pk=parent_id)
        else:
            parent = None
        name = data["name"]
        folder = Folder.objects.create(name=name)
        if parent:
            folder.move_to(parent, "last-child")
            folder.save()
        return JsonResponse({"success": True})

    def handle_folder(self, data):
        folder_id = int(data["id"])
        if folder_id:
            folder = Folder.objects.get(pk=folder_id)
            subfolders = folder.get_children()
            files = folder.files
        else:
            folder = None
            subfolders = Folder.objects.filter(parent=None)
            files = File.objects.filter(folder=None)

        return JsonResponse({"folder": {
            "id": folder.id if folder else 0,
            "name": folder.name if folder else "Root",
            "files": [_filer_file_to_json_dict(file) for file in files],
            "folders": [
                # Explicitly pass empty list of children to avoid recursion
                _filer_folder_to_json_dict(subfolder, children=())
                for subfolder in subfolders.order_by("name")
            ]
        }})

    def handle_upload(self):
        request = self.request
        folder_id = int(request.REQUEST["folder_id"])
        folder = Folder.objects.get(pk=folder_id)
        upload_file = handle_filedrop_upload(request)

        try:
            if upload_file.content_type.startswith("image/"):
                filer_file = filer_image_from_upload(request, path=folder, upload_data=upload_file)
            else:
                filer_file = filer_file_from_upload(request, path=folder, upload_data=upload_file)
        except Exception as exc:
            return JsonResponse({"error": force_text(exc)})

        return JsonResponse({"file": _filer_file_to_json_dict(filer_file)})
