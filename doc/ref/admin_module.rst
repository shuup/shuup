Admin Modules in Shuup
======================

Shuup provides a way to add custom modules to the admin site and provide configurations for the store and manage objects.

The first step is to subclass `AdminModule <shuup.admin.base.AdminModule>`.

You can take `TaxRulesAdminModule <shuup.default_tax.admin_module.TaxRulesAdminModule>` as a simple example of how to write a custom module.

Once you subclassed ``AdminModule``, now you must customize the information about your admin module. You must add a module ``name`` and optionally set a top level module breadcrumb entry using ``breadcrumbs_menu_entry``.

Se below what developers can implement in admin modules to make it outstanding. These tools enable Shuup to be highly customizable and extendable through addons.

Providing urls
--------------

The module can optionally provide urls to your custom admin views. They are returned through module's ``get_urls()`` method.
It must return a list of `admin_url <shuup.admin.utils.urls.admin_url>` which are pretty much normal Django urls with some additional options.

Providing menu entries
----------------------

The module can provide menu entries to be added in Shuup admin menus through ``get_menu_entries()``.
There are fixed categories to where your menu can be attached. You can take a look at the default admin modules code which categories are available.

Providing search results
------------------------

The module can provide results for a merchant's search in admin through ``get_search_results()``.
When merchant types into the search field, Shuup will pass the search term to each admin module and they can return the results along with urls to see more details of the result.

Providing dashboard blocks
--------------------------

The admin module can provide custom Dashboard blocks through ``get_dashboard_blocks()``.
Dashboard blocks are useful to summarize an information that is important to show on the admin dashboard, like charts and numbers.

Providing help blocks
---------------------

The admin module can provide help blocks through ``get_help_blocks()``.
These blocks helps merchants to setup the store and addons as quick as possible. They are quick links which will guide the merchants what to do before putting the store live.

Providing notifications
-----------------------

The admin module can provide notifications to present to merchant through ``get_notifications()``.
These notifications are helpful to warn or infor merchant about important things and you want him to see in dashboard with links to solve the issue. Examples of notifications could be low stocks level, tasks unfinished, orders waiting approval etc.


Providing model urls
--------------------

The module can implement ``get_model_url()`` to return an admin urls for a given object if it knows how to reverse that.
When custom addons have custom objects, the admin needs to know how to reverse an object to an url when merchants wants to edit the object or even access a list of those objects.
If no module returns anythings, it means the object is impossible to edit or list.


Permissions
-----------

Permissions are an important thing in Admin. Staff users should have groups attached so Shuup can check permissions for the user. Shuup doesn't use the Django's default permission system to handle permissions checks. Instead, it has a custom permissions utils that uses basically a string as the permissions key.

To limit non authorized users to access admin views, Shuup check permissions through the ``admin_url`` described above. You can inform the required permissions for each url if needed, but, by default, Shuup uses the view name as the permission key.

Along with admin urls, the entire admin module access can be revoked through permissions. This can be done by implementing the admin module ``get_required_permissions()`` method. By default, the module ``name`` is used as the permission string, this means that modules with duplicated names will conflict and one permission will enable/disable all of them.

When a module permission is revoked for an user, it doesn't mean he can't access the admin module urls. If the module permission is revoked, the user won't see the menu entry, the notifications, the menu and helper blocks and the search results won't work.
