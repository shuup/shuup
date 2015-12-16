import pytest
from filer.models import Folder, Image

from shoop.core.models import Shop, ShopStatus
from shoop.testing.factories import DEFAULT_IDENTIFIER, DEFAULT_NAME


@pytest.mark.django_db
def test_shop_wont_be_deleted():
    shop = Shop.objects.create(
        name=DEFAULT_NAME,
        identifier=DEFAULT_IDENTIFIER,
        status=ShopStatus.ENABLED,
        public_name=DEFAULT_NAME
    )

    folder = Folder.objects.create(name="Root")
    img = Image.objects.create(name="imagefile", folder=folder)

    shop.logo = img
    shop.save()
    img.delete()

    Shop.objects.get(pk=shop.pk)
