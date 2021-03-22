# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import JsonResponse
from django.test import override_settings
from django.test.client import RequestFactory
from django.utils.encoding import force_text
from filer.models import File, Folder
from six import BytesIO

from shuup.admin.modules.media.views import MediaBrowserView
from shuup.admin.shop_provider import set_shop
from shuup.admin.utils.permissions import set_permissions_for_group
from shuup.core.models import MediaFile, MediaFolder
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_media_view_images(rf):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop1 = factories.get_shop(identifier="shop1", enabled=True)
        shop1_staff1 = _create_random_staff(shop1)
        shop1_staff2 = _create_random_staff(shop1)

        group = factories.get_default_permission_group()
        set_permissions_for_group(group, ["media.upload-to-folder", "media.view-all"])

        shop2 = factories.get_shop(identifier="shop2", enabled=True)
        shop2_staff = _create_random_staff(shop2)

        shop1_staff1.groups.add(group)
        shop1_staff2.groups.add(group)
        shop2_staff.groups.add(group)

        # Let's agree this folder is created by for example carousel
        # so it would be shared with all the shops.
        folder = Folder.objects.create(name="Root")
        assert MediaFolder.objects.count() == 0
        path = "%s" % folder.name

        File.objects.create(name="normalfile", folder=folder)  # Shared between shops

        # Let's create 4 images for shop 1
        _mbv_upload(shop1, shop1_staff1, path=path)
        _mbv_upload(shop1, shop1_staff1, path=path)
        _mbv_upload(shop1, shop1_staff2, path=path)
        _mbv_upload(shop1, shop1_staff2, path=path)
        assert MediaFile.objects.count() == 4

        # Let's create 3 images for shop 2
        _mbv_upload(shop2, shop2_staff, path=path)
        _mbv_upload(shop2, shop2_staff, path=path)
        _mbv_upload(shop2, shop2_staff, path=path)
        assert MediaFile.objects.count() == 7

        # All files were created to same folder and while uploading
        # the each shop declared that they own the folder.
        assert Folder.objects.count() == 1
        assert MediaFolder.objects.count() == 1
        assert MediaFolder.objects.filter(shops=shop1).exists()
        assert shop1.media_folders.count() == 1
        assert shop1.media_files.count() == 4
        assert MediaFolder.objects.filter(shops=shop2).exists()
        assert shop2.media_folders.count() == 1
        assert shop2.media_files.count() == 3

        # Now let's make sure that each staff can view the folder
        # and all the files she should see.
        _check_that_staff_can_see_folder(rf, shop1, shop1_staff1, folder, 5)
        _check_that_staff_can_see_folder(rf, shop1, shop1_staff2, folder, 5)
        _check_that_staff_can_see_folder(rf, shop2, shop2_staff, folder, 4)


@pytest.mark.django_db
def test_edit_shared_folder(admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop1 = factories.get_shop(identifier="shop1", enabled=True)
        shop2 = factories.get_shop(identifier="shop2", enabled=True)

        folder = Folder.objects.create(name="Test folder")  # Shared folder
        folder_count = Folder.objects.count()

        response = _mbv_command(shop1, admin_user, {"action": "rename_folder", "id": folder.pk, "name": "Space"})
        assert not response["success"]
        response = _mbv_command(shop1, admin_user, {"action": "delete_folder", "id": folder.pk})
        assert not response["success"]

        # Let's make sure rename works when only one shop owns the folder
        media_folder = MediaFolder.objects.create(folder=folder)
        media_folder.shops.add(shop1)
        response = _mbv_command(shop1, admin_user, {"action": "rename_folder", "id": folder.pk, "name": "Space"})
        assert response["success"]
        assert Folder.objects.get(pk=folder.pk).name == "Space"

        # Then add second shop for the folder and let's check and
        # renaming should be disabled again.
        media_folder.shops.add(shop2)
        response = _mbv_command(shop1, admin_user, {"action": "rename_folder", "id": folder.pk, "name": "Space"})
        assert not response["success"]
        response = _mbv_command(shop1, admin_user, {"action": "delete_folder", "id": folder.pk})
        assert not response["success"]
        response = _mbv_command(shop2, admin_user, {"action": "delete_folder", "id": folder.pk})
        assert not response["success"]

        # Finally remove the folder as shop2
        media_folder.shops.remove(shop1)
        response = _mbv_command(shop1, admin_user, {"action": "delete_folder", "id": folder.pk})
        assert response["error"] == "Folder matching query does not exist."
        response = _mbv_command(shop2, admin_user, {"action": "delete_folder", "id": folder.pk})
        assert response["success"]
        assert Folder.objects.count() == folder_count - 1


@pytest.mark.django_db
def test_edit_shared_file(admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop1 = factories.get_shop(identifier="shop1", enabled=True)
        shop2 = factories.get_shop(identifier="shop2", enabled=True)

        folder1 = Folder.objects.create(name="folder1")
        folder2 = Folder.objects.create(name="folder2")
        file = File.objects.create(original_filename="test.jpg", folder=folder1)  # Shared file
        file_count = File.objects.count()
        assert force_text(file) == "test.jpg"

        response = _mbv_command(shop1, admin_user, {"action": "rename_file", "id": file.pk, "name": "test.tiff"})
        assert not response["success"]
        response = _mbv_command(shop1, admin_user, {"action": "move_file", "file_id": file.pk, "folder_id": folder2.pk})
        assert not response["success"]
        assert File.objects.get(pk=file.pk).folder == folder1
        response = _mbv_command(shop1, admin_user, {"action": "delete_file", "id": file.pk})
        assert not response["success"]

        # Let's make sure rename works when only one shop owns the file
        media_file = MediaFile.objects.create(file=file)
        media_file.shops.add(shop1)
        response = _mbv_command(shop1, admin_user, {"action": "rename_file", "id": file.pk, "name": "test.tiff"})
        assert response["success"]
        file = File.objects.get(pk=file.pk)
        assert force_text(file) == "test.tiff"

        # Let's move the file to different folder
        response = _mbv_command(shop1, admin_user, {"action": "move_file", "file_id": file.pk, "folder_id": folder2.pk})
        assert response["success"]
        assert File.objects.get(pk=file.pk).folder == folder2

        # Then add second shop for the file and let's check and
        # renaming should be disabled again.
        media_file.shops.add(shop2)
        response = _mbv_command(shop1, admin_user, {"action": "rename_file", "id": file.pk, "name": "test.tiff"})
        assert not response["success"]
        response = _mbv_command(shop1, admin_user, {"action": "delete_file", "id": file.pk})
        assert not response["success"]
        response = _mbv_command(shop2, admin_user, {"action": "rename_file", "id": file.pk, "name": "test.tiff"})
        assert not response["success"]
        response = _mbv_command(shop2, admin_user, {"action": "delete_file", "id": file.pk})
        assert not response["success"]

        # Finally remove the file as shop2
        media_file.shops.remove(shop1)
        response = _mbv_command(shop1, admin_user, {"action": "delete_file", "id": file.pk})
        assert response["error"] == "File matching query does not exist."
        response = _mbv_command(shop2, admin_user, {"action": "delete_file", "id": file.pk})
        assert response["success"]
        assert File.objects.count() == file_count - 1


def _mbv_command(shop, user, payload, method="post"):
    request = RequestFactory().generic(method, "/")
    request.user = user
    request.session = {}
    set_shop(request, shop)
    if method == "post":
        request._body = json.dumps(payload).encode("UTF-8")
    else:
        request.GET = payload

    mbv = MediaBrowserView.as_view()
    return json.loads(mbv(request).content.decode("UTF-8"))


def _mbv_upload(shop, user, **extra_data):
    content = ("42" * 42).encode("UTF-8")
    imuf = InMemoryUploadedFile(BytesIO(content), "file", "424242.pdf", "application/pdf", len(content), "UTF-8")
    request = RequestFactory().post("/", dict({"action": "upload", "file": imuf}, **extra_data))
    request.user = user
    request.session = {}
    set_shop(request, shop)

    view = MediaBrowserView.as_view()
    response = view(request)
    return json.loads(response.content.decode("UTF-8"))


def _create_random_staff(shop):
    user = factories.create_random_user(is_staff=True)
    shop.staff_members.add(user)
    return user


def _check_that_staff_can_see_folder(rf, shop, user, folder, expected_files_count):
    request = apply_request_middleware(rf.get("/", {"action": "folder", "id": folder.id}), user=user, shop=shop)
    view_func = MediaBrowserView.as_view()
    response = view_func(request)
    assert isinstance(response, JsonResponse)
    content = json.loads(response.content.decode("utf-8"))
    assert len(content["folder"]["files"]) == expected_files_count
