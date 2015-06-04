# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps.provides import override_provides
from shoop.front.templatetags.shoop_front import _get_helpers


class TestNs:
    name = "badgers"

    def snake(self):
        return True


def test_extendable_helper_ns():
    with override_provides("front_template_helper_namespace", [
        "%s:TestNs" % __name__
    ]):
        ns = _get_helpers()
        assert ns.badgers.snake()
