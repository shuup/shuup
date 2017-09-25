API Permissions
===============

You can configure the access level of your API through Shuup Admin panel for each endpoint found
by the :doc:`../ref/provides` at *Settings > Permissions > API*.

In order to make it work properly, make sure the permission class ``shuup.api.permissions.ShuupAPIPermission`` is
in the DRF ``DEFAULT_PERMISSION_CLASSES`` setting.

Our permission class will read your configuration set through admin and will apply it on the selected endpoints.

**Important**: Not only the access of the endpoint will be restricted but also the API documentation it provides will be restricted.

The available access levels are:

    * **Disabled** - No one can make requests.
    * **Admin users** (default) - Only administrators can make requests to the API to fetch, save, delete or update data.
    * **Authenticated users - Read/Write** - Any authenticated user can fetch, save, delete or update data.
    * **Authenticated users - Read** - Any authenticated user can only fetch data.
    * **Public users - Read/Write** - Any user (authenticated or not) can fetch, save, delete or update data. Use this with caution.
    * **Public users - Read** - Any user (authenticated or not) can only fetch data. Use this with caution.
