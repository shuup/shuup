from django.utils.translation import ugettext_lazy as _
from shuup.admin.base import AdminModule, MenuEntry

class MenuConfigurationModule(AdminModule):
    name = _("Menu Configuration")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:shop.list")

