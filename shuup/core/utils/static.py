# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from logging import getLogger

from django.utils.lru_cache import lru_cache

LOGGER = getLogger(__name__)


@lru_cache()
def get_shuup_static_url(path, package=None):
    """
    `path` is the static source path, e.g. myapp/styles.css
    `package` is the package name to get the version from.
        If not set, Shuup version is used. You can pass
        the name if any installed pacakge and use that
        version as a base.
    """
    from django.templatetags.static import static
    from shuup import __version__
    version = __version__

    if package:
        import pkg_resources
        try:
            distribution = pkg_resources.get_distribution(package)
            if distribution:
                version = distribution.version
        except pkg_resources.DistributionNotFound:
            LOGGER.exception("Failed to find the module {}".format(package))

    return "%s?v=%s" % (static(path), version)
