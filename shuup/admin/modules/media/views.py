# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.http.response import JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views.generic import TemplateView
from filer.models import File, Folder
from filer.models.imagemodels import Image

from shuup.admin.modules.media.utils import delete_folder
from shuup.admin.shop_provider import get_shop
from shuup.core.models import MediaFile, MediaFolder
from shuup.utils.excs import Problem
from shuup.utils.filer import filer_file_from_upload, filer_image_from_upload
from shuup.utils.mptt import get_cached_trees


def _filer_file_to_json_dict(file):
    """
    :type file: filer.models.File
    :rtype: dict
    """
    assert file.is_public

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
    :type file: filer.models.Folder|None
    :type children: list(filer.models.Folder)
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


def _ensure_media_folder(shop, folder):
    media_folder, created = MediaFolder.objects.get_or_create(folder=folder)
    if not media_folder.shops.filter(id=shop.id).exists():
        media_folder.shops.add(shop)


def _is_folder_shared(folder):
    if not settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
        return False

    media_folder = MediaFolder.objects.filter(folder=folder).first()
    if not media_folder:
        return True
    return bool(media_folder.shops.count() != 1)


def _get_folder_query_filter(shop):
    return Q(Q(media_folder__isnull=True) | Q(media_folder__shops__isnull=True) | Q(media_folder__shops=shop))


def _get_folder_query(shop, folder=None):
    queryset = Folder.objects.filter(_get_folder_query_filter(shop))
    if folder:
        queryset = queryset.filter(id=folder.id)
    return queryset


def _ensure_media_file(shop, file):
    media_file, created = MediaFile.objects.get_or_create(file=file)
    if not media_file.shops.filter(id=shop.id).exists():
        media_file.shops.add(shop)


def _is_file_shared(file):
    if not settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
        return False

    media_file = MediaFile.objects.filter(file=file).first()
    if not media_file:
        return True
    return bool(media_file.shops.count() != 1)


def _get_file_query(shop, folder=None):
    query = Q(is_public=True)
    query &= Q(Q(media_file__isnull=True) | Q(media_file__shops__isnull=True) | Q(media_file__shops=shop))
    queryset = File.objects.filter(query)
    if folder:
        queryset = queryset.filter(folder=folder)
    return queryset


def get_folder_name(folder):
    return (folder.name if folder else _("Root"))


def get_or_create_folder(shop, path):
    folders = path.split("/")
    parent = None
    child = None
    created = False
    for folder in folders:
        if folder != "":
            child, created = Folder.objects.get_or_create(parent=parent, name=folder)
            _ensure_media_folder(shop, child)
            parent = child
    return child


class MediaBrowserView(TemplateView):
    """
    A view for browsing media.

    Most of this is just a JSON API that the Javascript (`static_src/media/browser`) uses.
    """
    template_name = "shuup/admin/media/browser.jinja"
    title = ugettext_lazy("Browse Media")

    def get_context_data(self, **kwargs):
        context = super(MediaBrowserView, self).get_context_data(**kwargs)
        context["browser_config"] = {
            "filter": self.filter,
            "disabledMenus": self.disabledMenus
        }
        return context

    def get(self, request, *args, **kwargs):
        self.filter = request.GET.get("filter")
        self.disabledMenus = request.GET.get("disabledMenus", "").split(",")
        action = request.GET.get("action")
        handler = getattr(self, "handle_get_%s" % action, None)
        if handler:
            return handler(request.GET)
        return super(MediaBrowserView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action") or request.GET.get("action")
        if action == "upload":
            return media_upload(request, *args, **kwargs)

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
                return JsonResponse({"error": force_text(odne)}, status=400)
            except Problem as prob:
                return JsonResponse({"error": force_text(prob)})
        else:
            return JsonResponse({"error": "unknown action %s" % action})

    def handle_get_folders(self, data):
        shop = get_shop(self.request)
        root_folders = get_cached_trees(Folder._tree_manager.filter(_get_folder_query_filter(shop)))
        return JsonResponse({"rootFolder": _filer_folder_to_json_dict(None, root_folders)})

    def handle_post_new_folder(self, data):
        shop = get_shop(self.request)
        parent_id = int(data.get("parent", 0))
        if parent_id > 0:
            parent = _get_folder_query(shop).get(pk=parent_id)
        else:
            parent = None

        name = data["name"]
        folder = Folder.objects.create(name=name)
        if parent:
            folder.move_to(parent, "last-child")
            folder.save()

        _ensure_media_folder(shop, folder)
        return JsonResponse({"success": True, "folder": _filer_folder_to_json_dict(folder, ())})

    def handle_get_folder(self, data):
        shop = get_shop(self.request)
        try:
            folder_id = int(data.get("id", 0))
            if folder_id:
                folder = _get_folder_query(shop).get(pk=folder_id)
                subfolders = folder.get_children().filter(_get_folder_query_filter(shop))
                files = _get_file_query(shop, folder)
            else:
                folder = None
                subfolders = _get_folder_query(shop).filter(parent=None)
                files = _get_file_query(shop).filter(folder=None)
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
            "files": [_filer_file_to_json_dict(file) for file in files if file.is_public],
            "folders": [
                # Explicitly pass empty list of children to avoid recursion
                _filer_folder_to_json_dict(subfolder, children=())
                for subfolder in subfolders.order_by("name")
            ]
        }})

    def handle_post_rename_folder(self, data):
        shop = get_shop(self.request)
        folder = _get_folder_query(shop).get(pk=data["id"])
        if _is_folder_shared(folder):
            message = _("Can not rename shared folder.")
            return JsonResponse({"success": False, "message": message})

        folder.name = data["name"]
        folder.save(update_fields=("name",))
        return JsonResponse({"success": True, "message": _("Folder renamed.")})

    def handle_post_delete_folder(self, data):
        shop = get_shop(self.request)
        folder = _get_folder_query(shop).get(pk=data["id"])
        if _is_folder_shared(folder):
            message = _("Can not delete shared folder.")
            return JsonResponse({"success": False, "message": message})

        new_selected_folder_id = folder.parent_id
        message = delete_folder(folder)
        return JsonResponse({"success": True, "message": message, "newFolderId": new_selected_folder_id})

    def handle_post_rename_file(self, data):
        shop = get_shop(self.request)
        file = _get_file_query(shop).get(pk=data["id"])
        if _is_file_shared(file):
            message = _("Can not rename shared file.")
            return JsonResponse({"success": False, "message": message})

        file.name = data["name"]
        file.save(update_fields=("name",))
        return JsonResponse({"success": True, "message": _("File renamed.")})

    def handle_post_delete_file(self, data):
        shop = get_shop(self.request)
        file = _get_file_query(shop).get(pk=data["id"])
        if _is_file_shared(file):
            message = _("Can not delete shared file.")
            return JsonResponse({"success": False, "message": message})

        try:
            file.delete()
        except IntegrityError as ie:
            raise Problem(str(ie))
        return JsonResponse({"success": True, "message": _("File deleted.")})

    def handle_post_move_file(self, data):
        shop = get_shop(self.request)
        file = _get_file_query(shop).get(pk=data["file_id"])
        if _is_file_shared(file):
            message = _("Can not move shared file.")
            return JsonResponse({"success": False, "message": message})

        folder_id = int(data["folder_id"])
        if folder_id:
            folder = _get_folder_query(shop).get(pk=data["folder_id"])
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


def media_upload(request, *args, **kwargs):
    shop = get_shop(request)
    try:
        folder_id = int(request.POST.get("folder_id") or request.GET.get("folder_id") or 0)
        path = request.POST.get("path") or request.GET.get("path") or None
        if folder_id != 0:
            folder = _get_folder_query(shop).get(pk=folder_id)
        elif path:
            folder = get_or_create_folder(shop, path)
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

        _ensure_media_file(shop, filer_file)
    except Exception as exc:
        return JsonResponse({"error": force_text(exc)})

    return JsonResponse({
        "file": _filer_file_to_json_dict(filer_file),
        "message": _("%(file)s uploaded to %(folder)s") % {
            "file": filer_file.label,
            "folder": get_folder_name(folder)
        }
    })
