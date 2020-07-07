# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from enumfields import Enum

from shuup.utils.django_compat import reverse


class MenuExtenderLocation(Enum):
    MAIN_MENU = 1
    ADMIN_MENU = 2
    LEFT_MENU = 3
    FOOTER = 4


class FrontMenuExtender(object):
    location = MenuExtenderLocation.MAIN_MENU
    items = []
    menu_item_template = "menu_extension.jinja"

    def _get_template(self, theme):
        path_template = "shuup/%s/%s"
        try:
            template_name = path_template % (theme.template_dir, self.menu_item_template)
            return get_template(template_name)
        except Exception:
            template_name = path_template % ("xtheme", "menu_extension.jinja")  # super safe fallback
            return get_template(template_name)

    def get_rendered_menu_items(self, request, theme):
        template = self._get_template(theme)
        rendered_items = []
        for item in self.items:
            try:
                item["url"] = reverse(item["url"])
            except Exception:
                pass  # pass if the url is something like "#"

            rendered_template = template.render(item, request=request)
            rendered_items.append(rendered_template)
        return mark_safe("".join(rendered_items))
