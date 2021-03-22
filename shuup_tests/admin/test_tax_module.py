# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.encoding import force_text

from shuup.admin.module_registry import replace_modules
from shuup.admin.modules.taxes import TaxModule
from shuup.admin.modules.taxes.views import TaxClassEditView
from shuup.testing.factories import get_default_shop, get_default_tax_class
from shuup.testing.utils import apply_request_middleware
from shuup_tests.admin.utils import admin_only_urls


@pytest.mark.django_db
def test_tax_edit_view_works_at_all(rf, admin_user):
    get_default_shop()  # We need a shop to exists
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    request.user = admin_user

    default_tax_class = get_default_tax_class()

    with replace_modules([TaxModule]):
        with admin_only_urls():
            view_func = TaxClassEditView.as_view()
            response = view_func(request, pk=default_tax_class.pk)
            response.render()
            assert default_tax_class.name in force_text(response.content)
            response = view_func(request, pk=None)  # "new mode"
            response.render()
            assert response.content
