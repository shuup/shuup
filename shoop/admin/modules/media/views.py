# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http.response import JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l
from django.views.generic import TemplateView
from filer.models import File, Folder
from filer.models.imagemodels import Image
from mptt.utils import get_cached_trees

from shoop.admin.modules.media.utils import delete_folder
from shoop.utils.excs import Problem
from shoop.utils.filer import filer_file_from_upload, filer_image_from_upload


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
        "name": folder.name if folder else _("Root"),
        "children": [_filer_folder_to_json_dict(child) for child in children]
    }


def get_folder_name(folder):
    return (folder.name if folder else _("Root"))


class MediaBrowserView(TemplateView):
    """
    A view for browsing media.

    Most of this is just a JSON API that the Javascript (`static_src/media/browser`) uses.
    """
    template_name = "shoop/admin/media/browser.jinja"
    title = _l(u"Browse Media")

    def get_context_data(self, **kwargs):
        context = super(MediaBrowserView, self).get_context_data(**kwargs)
        context["browser_config"] = {
            "filter": self.filter
        }
        return context

    def get(self, request, *args, **kwargs):
        self.filter = request.REQUEST.get("filter")

        action = request.REQUEST.get("action")
        handler = getattr(self, "handle_get_%s" % action, None)
        if handler:
            return handler(request.REQUEST)
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
        handler = getattr(self, "handle_post_%s" % action, None)
        if handler:
            try:
                return handler(data)
            except ObjectDoesNotExist as odne:
                return JsonResponse({"error": force_text(odne)})
            except Problem as prob:
                return JsonResponse({"error": force_text(prob)})
        else:
            return JsonResponse({"error": "unknown action %s" % action})

    def handle_get_folders(self, data):
        root_folders = get_cached_trees(Folder._tree_manager.all())
        return JsonResponse({"rootFolder": _filer_folder_to_json_dict(None, root_folders)})

    def handle_post_new_folder(self, data):
        parent_id = int(data.get("parent", 0))
        if parent_id > 0:
            parent = Folder.objects.get(pk=parent_id)
        else:
            parent = None
        name = data["name"]
        folder = Folder.objects.create(name=name)
        if parent:
            folder.move_to(parent, "last-child")
            folder.save()
        return JsonResponse({"success": True, "folder": _filer_folder_to_json_dict(folder, ())})

    def handle_get_folder(self, data):
        try:
            folder_id = int(data.get("id", 0))
            if folder_id:
                folder = Folder.objects.get(pk=folder_id)
                subfolders = folder.get_children()
                files = folder.files
            else:
                folder = None
                subfolders = Folder.objects.filter(parent=None)
                files = File.objects.filter(folder=None)
        except ObjectDoesNotExist:
            return JsonResponse({
                "folder": None,
                "error": "Folder does not exist"
            })

        if self.filter == "images":
            files = files.instance_of(Image)

        return JsonResponse({"folder": {
            "id": folder.id if folder else 0,
            "name": get_folder_name(folder),
            "files": [_filer_file_to_json_dict(file) for file in files],
            "folders": [
                # Explicitly pass empty list of children to avoid recursion
                _filer_folder_to_json_dict(subfolder, children=())
                for subfolder in subfolders.order_by("name")
            ]
        }})

    def handle_upload(self):
        request = self.request

        try:
            folder_id = int(request.REQUEST.get("folder_id", 0))
            if folder_id != 0:
                folder = Folder.objects.get(pk=folder_id)
            else:
                folder = None  # Root folder upload. How bold!
        except Exception as exc:
            return JsonResponse({"error": "Invalid folder: %s" % force_text(exc)})

        try:
            upload_file = request.FILES["file"]

            if upload_file.content_type.startswith("image/"):
                filer_file = filer_image_from_upload(request, path=folder, upload_data=upload_file)
            else:
                filer_file = filer_file_from_upload(request, path=folder, upload_data=upload_file)
        except Exception as exc:
            return JsonResponse({"error": force_text(exc)})

        return JsonResponse({
            "file": _filer_file_to_json_dict(filer_file),
            "message": _("%(file)s uploaded to %(folder)s") % {
                "file": filer_file.label,
                "folder": get_folder_name(folder)
            }
        })

    def handle_post_rename_folder(self, data):
        folder = Folder.objects.get(pk=data["id"])
        folder.name = data["name"]
        folder.save(update_fields=("name",))
        return JsonResponse({"success": True, "message": _("Folder renamed.")})

    def handle_post_delete_folder(self, data):
        folder = Folder.objects.get(pk=data["id"])
        new_selected_folder_id = folder.parent_id
        message = delete_folder(folder)
        return JsonResponse({"success": True, "message": message, "newFolderId": new_selected_folder_id})

    def handle_post_rename_file(self, data):
        file = File.objects.get(pk=data["id"])
        file.name = data["name"]
        file.save(update_fields=("name",))
        return JsonResponse({"success": True, "message": _("File renamed.")})

    def handle_post_delete_file(self, data):
        file = File.objects.get(pk=data["id"])
        try:
            file.delete()
        except IntegrityError as ie:
            raise Problem(str(ie))
        return JsonResponse({"success": True, "message": _("File deleted.")})

    def handle_post_move_file(self, data):
        file = File.objects.get(pk=data["file_id"])
        folder_id = int(data["folder_id"])
        if folder_id:
            folder = Folder.objects.get(pk=data["folder_id"])
        else:
            folder = None
        old_folder = file.folder
        file.folder = folder
        file.save(update_fields=("folder",))
        return JsonResponse({
            "success": True,
            "message": _("%(file)s moved from %(old)s to %(new)s.") % {
                "file": file,
                "old": get_folder_name(old_folder),
                "new": get_folder_name(folder)
            }
        })
