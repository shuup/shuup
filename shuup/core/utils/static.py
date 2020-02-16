# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


def get_shuup_static_url(path):
    from django.contrib.staticfiles.templatetags.staticfiles import static
    from shuup import __version__
    return "%s?v=%s" % (static(path), __version__)
