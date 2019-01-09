# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import csv

import pytest
from django.http import HttpResponse
from shuup.admin.utils.picotable import PicotableMassAction, PicotableFileMassAction
from shuup.core.models import Product
from shuup.testing.factories import get_default_shop, get_default_supplier, create_product
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish

class TestPicotableMassAction(PicotableMassAction):

    def process(self, request, ids):
        Product.objects.filter(id__in=ids).update(cost_center="test")


class TestPicotableFileMassAction(PicotableFileMassAction):

    def process(self, request, ids):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        writer = csv.writer(response, delimiter=";")
        writer.writerow(["test", "testing"])
        for product in Product.objects.filter(id__in=ids):
            writer.writerow([product.pk, product.sku])
        return response


@pytest.mark.django_db
def test_mass_actions(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)

    ids = [product.id, product2.id]
    request = apply_request_middleware(rf.get("/"), user=admin_user)

    TestPicotableMassAction().process(request, ids)
    for product in Product.objects.all():
        assert product.cost_center == "test"

    mass_action_response = TestPicotableFileMassAction().process(request, ids)
    assert mass_action_response["Content-disposition"] == 'attachment; filename="products.csv"'
