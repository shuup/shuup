# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.apps.provides import override_provides
from shuup.testing.factories import get_default_shop
from shuup.utils.django_compat import reverse
from shuup.xtheme.extenders import FrontMenuExtender
from shuup_tests.utils import SmartClient


class TestExtender(FrontMenuExtender):
    items = [{"url": "shuup:index", "title": "Test Link to Front"}]


@pytest.mark.django_db
def test_extender_renders_main_menu(rf):
    get_default_shop()

    with override_provides("front_menu_extender", ["shuup_tests.xtheme.test_extenders:TestExtender"]):
        c = SmartClient()
        soup = c.soup(reverse("shuup:index"))
        link_texts = [a.text for a in soup.findAll("a")]
        assert "Test Link to Front" in link_texts
