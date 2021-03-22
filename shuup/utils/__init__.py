# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import sys
from django.utils.translation import ugettext_lazy as _

import shuup.apps


def update_module_attributes(object_names, module_name):
    """
    Update __module__ attribute of objects in module.

    Set the ``__module__`` attribute of the objects (resolved by the
    given object names from the given module name) to `module_name`.

    Use case for this function in Shuup is to hide the actual location
    of objects imported from private submodules, so that they will show
    up nicely in the Sphinx generated API documentation.  This is done
    by appending following line to the end of the ``__init__.py`` of the
    main package::

      update_module_attributes(__all__, __name__)

    :type object_names: Iterable[str]
    :param object_names:
      Names of the objects to update.
    :type module_name: str
    :param module_name:
      Name of the module where the objects reside and also the new value
      which will be assigned to ``__module__`` attribute of each object.
    """
    module = sys.modules[module_name]
    for object_name in object_names:
        getattr(module, object_name).__module__ = module_name


class ShuupUtilsAppConfig(shuup.apps.AppConfig):
    name = __name__
    verbose_name = _("Shuup Utilities")
    label = "shuup_utils"


default_app_config = __name__ + ".ShuupUtilsAppConfig"

# There's a small elephant in this file.

#       ,
#      ((_,-.
#       '-.\_)'-,
#          )  _ )'-   PjP
# ,.;.,;,,(/(/ \));,;.,.,
