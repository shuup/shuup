# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django
import json
import mock
import pytest
import tempfile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import ProtectedError
from django.http import JsonResponse
from django.test import override_settings
from django.test.client import RequestFactory
from django.utils.encoding import force_text
from filer.models import File, Folder, Image
from six import BytesIO

from shuup.admin.modules.media.views import MediaBrowserView
from shuup.admin.utils.permissions import set_permissions_for_group
from shuup.testing import factories
from shuup.testing.factories import generate_image, get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup.utils.filer import can_see_root_folder, ensure_media_folder, get_or_create_folder
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
@pytest.mark.parametrize("is_public, expected_file_count", [(False, 0), (True, 1)])
def test_media_view_images(rf, admin_user, is_public, expected_file_count):
    shop = get_default_shop()
    folder = get_or_create_folder(shop, "Root")
    File.objects.create(name="normalfile", folder=folder)
    img = Image.objects.create(name="imagefile", folder=folder, is_public=is_public)

    request = apply_request_middleware(
        rf.get("/", {"filter": "images", "action": "folder", "id": folder.id}), user=admin_user
    )
    request.user = admin_user
    view_func = MediaBrowserView.as_view()
    response = view_func(request)
    assert isinstance(response, JsonResponse)
    content = json.loads(response.content.decode("utf-8"))
    assert len(content["folder"]["files"]) == expected_file_count
    if expected_file_count:
        filedata = content["folder"]["files"][0]
        assert filedata["name"] == img.name


@pytest.mark.django_db
def test_media_view_images_without_root_access(rf):
    shop = factories.get_default_shop()
    staff_user = factories.UserFactory(is_staff=True)
    permission_group = factories.get_default_permission_group()
    staff_user.groups.add(permission_group)
    shop.staff_members.add(staff_user)
    set_permissions_for_group(permission_group, ["upload-media"])

    assert not can_see_root_folder(staff_user)

    folder = get_or_create_folder(shop, "Root")
    File.objects.create(name="normalfile", folder=folder)
    img = Image.objects.create(name="imagefile", folder=folder, is_public=True)

    request = apply_request_middleware(rf.get("/", {"filter": "images", "action": "folder"}), user=staff_user)
    request.user = staff_user
    view_func = MediaBrowserView.as_view()
    response = view_func(request)
    assert isinstance(response, JsonResponse)
    content = json.loads(response.content.decode("utf-8"))
    assert len(content["folder"]["folders"]) == 0
    assert len(content["folder"]["files"]) == 0


def mbv_command(user, payload, method="post"):
    request = RequestFactory().generic(method, "/")
    request.user = user
    if method == "post":
        request._body = json.dumps(payload).encode("UTF-8")
    else:
        request.GET = payload
    mbv = MediaBrowserView.as_view()
    return json.loads(mbv(request).content.decode("UTF-8"))


def mbv_upload(user, **extra_data):
    content = ("42" * 42).encode("UTF-8")
    imuf = InMemoryUploadedFile(BytesIO(content), "file", "424242.pdf", "application/pdf", len(content), "UTF-8")
    request = RequestFactory().post("/", dict({"action": "upload", "file": imuf}, **extra_data))
    request.user = user
    view = MediaBrowserView.as_view()
    response = view(request)
    return json.loads(response.content.decode("UTF-8"))


def get_id_tree(folders_response):
    if "rootFolder" in folders_response:
        folders_response = folders_response["rootFolder"]
    children = {}

    def walk(target, node):
        for kid in node.get("children", ()):
            walk(target.setdefault(kid["id"], {}), kid)

    walk(children, folders_response)
    return children


@pytest.mark.django_db
def test_new_folder(admin_user):
    shop = get_default_shop()
    folder1 = get_or_create_folder(shop, printable_gibberish())
    child_folder_data = mbv_command(admin_user, {"action": "new_folder", "name": "y", "parent": folder1.id})["folder"]
    assert Folder.objects.get(pk=child_folder_data["id"]).parent == folder1
    root_folder_data = mbv_command(admin_user, {"action": "new_folder", "name": "y"})["folder"]
    assert not Folder.objects.get(pk=root_folder_data["id"]).parent_id


@pytest.mark.django_db
def test_get_folder(admin_user):
    shop = get_default_shop()
    folder1 = get_or_create_folder(shop, printable_gibberish())
    folder2 = get_or_create_folder(shop, printable_gibberish())
    folder2.parent = folder1
    folder2.save()

    root_resp = mbv_command(admin_user, {"action": "folder"}, "GET")
    assert any(f["id"] == folder1.pk for f in root_resp["folder"]["folders"])
    f1_resp = mbv_command(admin_user, {"action": "folder", "id": folder1.pk}, "GET")
    assert f1_resp["folder"]["folders"][0]["id"] == folder2.pk
    assert not f1_resp["folder"]["files"]
    assert f1_resp["folder"]["name"] == folder1.name
    assert mbv_command(admin_user, {"action": "folder", "id": -1}, "GET")["error"]


@pytest.mark.django_db
def test_rename_folder(admin_user):
    shop = get_default_shop()
    folder = get_or_create_folder(shop, printable_gibberish())
    mbv_command(admin_user, {"action": "rename_folder", "id": folder.pk, "name": "Space"})
    assert Folder.objects.get(pk=folder.pk).name == "Space"


@pytest.mark.django_db
def test_delete_folder(admin_user):
    shop = get_default_shop()
    folder = get_or_create_folder(shop, printable_gibberish())
    mbv_command(admin_user, {"action": "delete_folder", "id": folder.pk})
    assert not Folder.objects.filter(pk=folder.pk).exists()


@pytest.mark.django_db
def test_rename_file(admin_user):
    file = File.objects.create(original_filename="test.jpg")
    assert force_text(file) == "test.jpg"
    assert file.pk
    mbv_command(admin_user, {"action": "rename_file", "id": file.pk, "name": "test.tiff"})
    file = File.objects.get(pk=file.pk)
    assert force_text(file) == "test.tiff"


@pytest.mark.django_db
def test_delete_file(admin_user):
    file = File.objects.create()
    assert file.pk
    mbv_command(admin_user, {"action": "delete_file", "id": file.pk})
    assert not File.objects.filter(pk=file.pk).exists()


@pytest.mark.django_db
def test_move_file(admin_user):
    shop = get_default_shop()
    folder1 = get_or_create_folder(shop, printable_gibberish())
    folder2 = get_or_create_folder(shop, printable_gibberish())
    file = File.objects.create(folder=folder1)
    mbv_command(admin_user, {"action": "move_file", "file_id": file.pk, "folder_id": folder2.pk})
    assert File.objects.get(pk=file.pk).folder == folder2
    mbv_command(admin_user, {"action": "move_file", "file_id": file.pk, "folder_id": 0})
    assert File.objects.get(pk=file.pk).folder is None


@pytest.mark.django_db
def test_auto_error_handling(admin_user):
    assert mbv_command(admin_user, {"action": "rename_file", "id": -1})["error"]


@pytest.mark.django_db
def test_upload(rf, admin_user):
    shop = get_default_shop()
    response = mbv_upload(admin_user)
    assert not File.objects.get(pk=response["file"]["id"]).folder
    folder = get_or_create_folder(shop, printable_gibberish())
    response = mbv_upload(admin_user, folder_id=folder.pk)
    assert File.objects.get(pk=response["file"]["id"]).folder == folder


@pytest.mark.django_db
def test_upload_invalid_filetype(rf, admin_user):
    assert File.objects.count() == 0
    content = ("42" * 42).encode("UTF-8")
    imuf = InMemoryUploadedFile(BytesIO(content), "file", "424242.exe", "text/plain", len(content), "UTF-8")
    request = RequestFactory().post("/", dict({"action": "upload", "file": imuf}))
    request.user = admin_user
    view = MediaBrowserView.as_view()
    response = view(request)
    error_message = json.loads(response.content.decode("UTF-8"))
    assert "extension 'exe' is not allowed" in error_message["error"]["file"][0]
    assert File.objects.count() == 0


@pytest.mark.django_db
def test_upload_into_new_folder(rf, admin_user):
    assert Folder.objects.count() == 0
    # no folder
    response = mbv_upload(admin_user, path="/")
    assert not File.objects.get(pk=response["file"]["id"]).folder
    assert Folder.objects.count() == 0

    # new folder
    response = mbv_upload(admin_user, path="/foo/bar")
    folder = File.objects.get(pk=response["file"]["id"]).folder
    assert folder.name == "bar"
    assert folder.parent.name == "foo"
    assert not folder.parent.parent
    assert Folder.objects.count() == 2

    # ensure path is correct with same folder names
    response = mbv_upload(admin_user, path="/bar/foo")
    folder = File.objects.get(pk=response["file"]["id"]).folder
    assert folder.name == "foo"
    assert folder.parent.name == "bar"
    assert not folder.parent.parent
    assert Folder.objects.count() == 4

    # upload into pre-existing folder
    response = mbv_upload(admin_user, path="/foo/bar")
    folder = File.objects.get(pk=response["file"]["id"]).folder
    assert folder.name == "bar"
    assert folder.parent.name == "foo"
    assert not folder.parent.parent
    assert Folder.objects.count() == 4

    # add subfolder
    response = mbv_upload(admin_user, path="/foo/bar/baz")
    folder = File.objects.get(pk=response["file"]["id"]).folder
    assert folder.name == "baz"
    assert folder.parent.name == "bar"
    assert folder.parent.parent.name == "foo"
    assert Folder.objects.count() == 5


@pytest.mark.django_db
def test_get_folders(rf, admin_user):
    shop = get_default_shop()

    # Create a structure and retrieve it
    folder1 = get_or_create_folder(shop, printable_gibberish())
    folder2 = get_or_create_folder(shop, printable_gibberish())
    folder3 = get_or_create_folder(shop, printable_gibberish())

    folder4 = get_or_create_folder(shop, printable_gibberish())
    folder4.parent = folder2
    folder4.save()

    folder5 = get_or_create_folder(shop, printable_gibberish())
    folder5.parent = folder3
    folder5.save()

    tree = get_id_tree(mbv_command(admin_user, {"action": "folders"}, "GET"))
    assert set((folder1.id, folder2.id, folder3.id)) <= set(tree.keys())
    assert folder4.pk in tree[folder2.pk]
    assert folder5.pk in tree[folder3.pk]


@pytest.mark.django_db
def test_get_folders_without_view_all_permission(rf):
    shop = factories.get_default_shop()
    staff_user = factories.UserFactory(is_staff=True)
    permission_group = factories.get_default_permission_group()
    staff_user.groups.add(permission_group)
    shop.staff_members.add(staff_user)
    set_permissions_for_group(permission_group, ["upload-media"])

    assert not can_see_root_folder(staff_user)

    # Create a structure and retrieve it
    folder1 = get_or_create_folder(shop, printable_gibberish())
    folder1_media_folder = ensure_media_folder(shop, folder1)
    folder1_media_folder.owners.add(staff_user)
    folder2 = get_or_create_folder(shop, printable_gibberish())
    folder3 = get_or_create_folder(shop, printable_gibberish())

    folder4 = get_or_create_folder(shop, printable_gibberish())
    folder4.parent = folder2
    folder4.save()
    folder4_media_folder = ensure_media_folder(shop, folder4)
    folder4_media_folder.owners.add(staff_user)

    folder5 = get_or_create_folder(shop, printable_gibberish())
    folder5.parent = folder4
    folder5.save()

    folder6 = get_or_create_folder(shop, printable_gibberish())
    folder6.parent = folder5
    folder6.save()
    folder6_media_folder = ensure_media_folder(shop, folder6)
    folder6_media_folder.owners.add(staff_user)

    folder7 = get_or_create_folder(shop, printable_gibberish())
    folder7.parent = folder6
    folder7.save()

    tree = get_id_tree(mbv_command(staff_user, {"action": "folders"}, "GET"))
    assert set((folder1.id, folder4.id)) <= set(tree.keys())


@pytest.mark.django_db
def test_deleting_mid_folder(rf, admin_user):
    shop = get_default_shop()

    folder1 = get_or_create_folder(shop, printable_gibberish(), admin_user)

    folder2 = get_or_create_folder(shop, printable_gibberish(), admin_user)
    folder2.parent = folder1
    folder2.save()

    folder3 = get_or_create_folder(shop, printable_gibberish(), admin_user)
    folder3.parent = folder2
    folder3.save()
    tree = get_id_tree(mbv_command(admin_user, {"action": "folders"}, "GET"))
    assert tree[folder1.pk] == {folder2.pk: {folder3.pk: {}}}
    mbv_command(admin_user, {"action": "delete_folder", "id": folder2.pk})
    tree = get_id_tree(mbv_command(admin_user, {"action": "folders"}, "GET"))
    assert tree[folder1.pk] == {folder3.pk: {}}
    folder1 = Folder.objects.get(pk=folder1.pk)
    assert list(folder1.get_children()) == [folder3]


@pytest.mark.django_db
def test_delete_protected_folder(rf, admin_user):
    shop = get_default_shop()

    folder1 = get_or_create_folder(shop, printable_gibberish(), admin_user)

    folder2 = get_or_create_folder(shop, printable_gibberish(), admin_user)
    folder2.parent = folder1
    folder2.save()

    with mock.patch(
        "filer.models.foldermodels.Folder.delete",
        side_effect=ProtectedError("Cannot delete", [folder2]),
    ) as mocked:
        mbv_command(admin_user, {"action": "delete_folder", "id": folder2.pk})
        mocked.assert_called()
    folder1 = Folder.objects.get(pk=folder1.pk)
    assert list(folder1.get_children()) == [folder2]

    mbv_command(admin_user, {"action": "delete_folder", "id": folder2.pk})
    folder1 = Folder.objects.get(pk=folder1.pk)
    assert list(folder1.get_children()) == []
    assert not Folder.objects.filter(pk=folder2.pk).exists()


@pytest.mark.django_db
def test_upload_invalid_image(rf, admin_user):
    assert File.objects.count() == 0
    content = ("32" * 32).encode("UTF-8")
    imuf = InMemoryUploadedFile(BytesIO(content), "file", "424242.png", "image/png", len(content), "UTF-8")
    request = RequestFactory().post("/", dict({"action": "upload", "file": imuf}))
    request.user = admin_user
    view = MediaBrowserView.as_view()
    response = view(request)
    error_message = json.loads(response.content.decode("UTF-8"))
    assert "not an image or a corrupted image." in error_message["error"]["file"][0]
    assert File.objects.count() == 0


@pytest.mark.django_db
def test_upload_valid_image(client, rf, admin_user):
    assert File.objects.count() == 0

    tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
    generate_image(120, 120).save(tmp_file)
    # tmp_file.seek(0)
    client.login(username="admin", password="password")
    with open(tmp_file.name, "rb") as data:
        response = client.post(
            reverse("shuup_admin:media.upload"), data=dict({"action": "upload", "file": data}), format="multipart"
        )

    assert File.objects.count() == 1


@pytest.mark.django_db
def test_large_image(client, rf, admin_user):
    assert File.objects.count() == 0
    with override_settings(SHUUP_MAX_UPLOAD_SIZE=10):
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        generate_image(120, 120).save(tmp_file)
        # tmp_file.seek(0)
        client.login(username="admin", password="password")
        with open(tmp_file.name, "rb") as data:
            response = client.post(
                reverse("shuup_admin:media.upload"), data=dict({"action": "upload", "file": data}), format="multipart"
            )
            assert response.status_code == 400
            data = json.loads(response.content.decode("utf-8"))
            assert "Maximum file size reached" in data["error"]["file"][0]

    assert File.objects.count() == 0
