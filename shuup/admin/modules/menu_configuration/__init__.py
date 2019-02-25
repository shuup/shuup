from django.utils.translation import ugettext_lazy as _
from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.utils.urls import (
    admin_url, derive_model_url, get_edit_and_list_urls, get_model_url
)

class MenuConfigurationModule(AdminModule):
    name = _("Menu Configuration")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:menu_configuration")

    def get_urls(self):
        return [
            admin_url(
                "^menu-configuration/$",
                "shuup.admin.modules.menu_configuration.views.MenuConfigurationListView",
                name="menu_configuration.list"
            ),
        ]
