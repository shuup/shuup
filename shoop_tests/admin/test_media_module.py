import json

from django.http import JsonResponse
from filer.models import File, Folder
from filer.models.imagemodels import Image
import pytest
from shoop.admin.modules.media.views import MediaBrowserView
from shoop.testing.factories import get_default_shop
from shoop_tests.utils import apply_request_middleware


@pytest.mark.django_db
def test_media_view_images(rf):
    get_default_shop()
    folder = Folder.objects.create(name="Root")
    file = File.objects.create(name="normalfile", folder=folder)
    img = Image.objects.create(name="imagefile", folder=folder)

    request = apply_request_middleware(rf.get("/sa/media", {"filter": "images", "action": "folder", "id": folder.id}))
    view_func = MediaBrowserView.as_view()
    response = view_func(request)
    assert isinstance(response, JsonResponse)
    content = json.loads(response.content.decode("utf-8"))
    assert len(content["folder"]["files"]) == 1
    filedata = content["folder"]["files"][0]
    assert filedata["name"] == img.name

