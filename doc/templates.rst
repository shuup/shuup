Template Design
===============

This part of the documentation covers the structural elements of Shuup's default
templates and instructs you on how to create your own customized templates.

To be able to create customized templates you'll need to have understanding of the
principles of HTML and CSS.

If you would like to start creating your own customized templates with these
instructions you should already have a working Shuup installation with the
default frontend theme up and running. If not, you can start by reading
:doc:`Getting Started guide <getting_started_dev>`.

Shuup's default frontend theme
------------------------------

Shuup's frontend templates are written with `Jinja2 <http://jinja.pocoo.org/>`_
which is a templating engine for Python very similar to Django’s templates.

The default frontend theme uses the `Bootstrap 3 <http://getbootstrap.com/>`_ framework, which
consists of Bootstrap's HTML structure and Bootstrap specified CSS classes.
If you want to create your own templates, it would require using Bootstrap 3
or overwriting all the template files with your custom HTML structure and HTML
classes.

Shuup's template files are easy to modify and basic knowledge of HTML and CSS
takes you far. Shuup's frontend and the default theme already include the necessary
template tags to print out all the features a basic shop would need.
It is fairly simple to add your custom HTML elements around
template tags and customize your shop to your needs.


Template folder structure
^^^^^^^^^^^^^^^^^^^^^^^^^

Shuup utilizes a similar folder structure for all the templates in different apps.
All the template files are always included in the app folder ``shuup/APP/templates/``.

Within this template folder the folder structure is: ``APP/MODULE/TEMPLATE.jinja``.
For example, this could be converted into ``shuup/product/detail.jinja``

The default frontend theme can be found in ``shuup/themes/classic_gray``.

.. topic:: Example

   The Simple CMS module has a template to show pages created with it.
   This ``page.jinja`` template can be found under the Simple CMS template
   folder: ``shuup/simple_cms/templates/`` where the path to the template file
   is ``shuup/simple_cms/page.jinja``.

Other default features such as user authentication, customer
info, order history, registration and search etc. can be found in their own
application templates under ``shuup/front/apps/``. Each app has it's own
template folder containing application specific templates.

Templates have been split into separate files and each file has its own
purpose. Template files inherit the base layout from ``shuup/base.jinja``.


General
^^^^^^^

General template files can be found under ``shuup/front/templates/``

**Base** ``shuup/front/base.jinja``
    Defines the structure of your templates. It includes the ``<html>``,
    ``<head>`` and ``<body>`` tags, and the general structure of all frontend
    pages (unless explicitly overridden).

**Index** ``shuup/front/index.jinja``
    Your shop's home page.

**Macros** ``shuup/front/macros.jinja``
    Additional template macros that can be used in other template files. For
    example single product box is rendered with a macro, where it can be called
    with customized parameters. Also form fields, alerts and order details can
    be generated with macros.

**Includes** ``shuup/front/includes/``
    Additional HTML that can be included in pages. In the default frontend theme all
    the included filenames start with ``_``. All navigation related HTML and
    template tags are included to ``base.jinja`` and for example you could
    create a ``_footer.jinja`` to be included if needed.


Products and Categories
^^^^^^^^^^^^^^^^^^^^^^^

Product and category templates can be found under ``shuup/front/templates/``

**Detail** ``shuup/front/product/detail.jinja``
    The view for a single product. Displays a product and its details.
    The file uses template tags to include product attributes and ordering sections.

**Category** ``shuup/front/product/category.jinja``
    A view for a single category.
    This template lists all the products of the selected category.

Shopping basket
^^^^^^^^^^^^^^^

All shopping basket related templates go in the ``shuup/front/templates/shuup/front/basket``
folder. This includes the default structure of the shopping basket and additional
shopping basket elements.

The default shopping basket template also includes the ordering form.
This does not apply to shops using multi-phase checkout.

**Default Basket** ``shuup/front/basket/default_basket.jinja``
    The structure of shopping basket. It includes the shopping basket's
    contents as a table from a separate macro in ``shuup/front/templates/shuup/front/macros/basket.jinja``.
    The ordering form macro is also being rendered in this file.

Orders
^^^^^^

Order related templates can be found in ``shuup/front/templates/shuup/front/order/``.

**Complete** ``shuup/front/order/complete.jinja``
    Displays the order success message and details of the order.

**Payment Canceled** ``shuup/front/order/payment_canceled.jinja``
    Template for displaying payment cancellation.


Simple Search
^^^^^^^^^^^^^

Simple Search is its own application that can be found in the front apps folder:
``shuup/apps/simple_search/templates``

**Search** ``shuup/simple_search/search.jinja``
    The search template includes the search form,
    search result sorting options and a list of search results.


Authentication
^^^^^^^^^^^^^^

Authentication through the Shuup Front is another sub-app.
Its templates can be found in its own folder:
``shuup/front/apps/auth/templates/shuup/user/``

**Login and Logout**
    Templates for login form and logout message pages.

**Password Recovery**
    Password recovery process including the templates for shop and e-mail.


Registration
^^^^^^^^^^^^

Registration is another sub-app.
Its templates can be found in:
``shuup/front/apps/registration/templates``

**Registration Form** ``shuup/registration/register.jinja``
    Registration form template for new users.

**Activation Failed** ``shuup/registration/activation_failed.jinja``
    A template for displaying an error message when account activation fails.


Customer Information
^^^^^^^^^^^^^^^^^^^^

Customer information is another sub-app.
Its templates can be found in:
``shuup/front/apps/customer_information/templates/``

**Edit** ``shuup/customer_information/edit.jinja``
    Template for editing customer details.


Personal Order History
^^^^^^^^^^^^^^^^^^^^^^

Personal Order History, another sub-app, naturally has its templates in its own folder.
``shuup/front/apps/personal_order_history/templates/``

**Order Detail** ``shuup/personal_order_history/order_detail.jinja``
    Template for displaying single order's details.

**Order List** ``shuup/personal_order_history/order_list.jinja``
    Template for listing all the previous personal orders.


.. _custom-template-helper-functions:

Custom Template Helper Functions
--------------------------------

This paragraph explains how to register template functions in Shuup's sub-apps.
If you are interested in ``Jinja2``'s way to do it,
please refer to the `Jinja2 documentation <http://jinja.pocoo.org/>`_.

The AppConfig
^^^^^^^^^^^^^

The ``front_template_helper_namespace`` category in the ``provides`` dictionary
tells the framework that there are template helper functions to be found in the
namespace class (``TemplateHelper``) given.

For more information about ``provides`` please refer to the `documentation <doc/provides.rst>`_

The TemplateHelper class
^^^^^^^^^^^^^^^^^^^^^^^^

This class contains all the functions that the are exposed for frontend templates.

Using helpers in a template
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The template helpers can be used in templates with ``shuup.<module_name>.<TemplateHelper::method>()``.
For example ``shuup.my_module.get_day_names()``.


Static files
------------

Static files such as images, stylesheets and scripts go under the static
folder, using the `Django staticfiles framework <https://docs.djangoproject.com/en/1.8/howto/static-files/>`.

You can access static data files in templates by using the ``{{ static() }}`` function.
For example, if you have ``img/image.jpg`` in your static files, generating
a ``src`` for an ``<img>`` tag would be as easy as ``<img src="{{ static(img/image.jpg") }}">``.

Creating custom templates
-------------------------

You may either derive your own theme from the default theme, or write your own from scratch.

The basic principle of deriving custom Shuup templates is not to modify the
original files (default frontend themes) within the app directory, but to copy them
into to your own application's template directory.
If your own application is listed before ``shuup.front`` (and/or other theme apps)
in Django's ``INSTALLED_APPS`` configuration, Django will prefer your templates
over others with the same path.

This means it is possible to overwrite only some of the default files or
all of them. If there is no customized template with the same path and filename,
Django will use the default file instead.

All the template files that you want to customize go under your application's
template folder in the same folder hierarchy as under the original app's ``templates``
folder. The folder hierarchy for frontend templates was discussed earlier in this document.

.. topic:: Example

  Let's say you only would like to make a customized home page for your shop,
  but leave all other templates as they are. Let's call your application ``myshop``.

  Simply copy ``index.jinja`` from ``shuup/front/templates/shuup/index.jinja``
  to your application's template folder ``myshop/templates/shuup/index.jinja``,
  then modify it to your heart's content.

  Now let's say you want to tweak the product category view too.

  Copy ``shuup/front/templates/shuup/product/category.jinja`` to
  ``myshop/templates/shuup/product/category.jinja``, then start modifying.
  As you can see, the template directory structure within your ``myshop`` application
  reflects the one in the original app.

Overriding templates and macros
-------------------------------

The general ideology with overriding templates and themes:
* macros: simple block changes
* templates: totally different structure

Most of the Shuup Front templates are found in ``shuup/front/templates/shuup/front/``
and macros in ``shuup/front/templates/shuup/front/macros``.

Shuup has some applications for front also, these are found in ``shuup/front/apps``.
These apps define their own templates and are not found
in the ``shuup_shuup/front/templates/shuup/front/``.

**For example purposes, we expect that your theme is defined like this**

.. code-block:: python

    class MyTheme(ClassicGrayTheme):
        template_dir = "mytheme"

.. topic:: Note

    This means that your templates are found in ``templates/mytheme/shuup/``.

    ``templates/mytheme/shuup/front/index.jinja`` **must exist**.

Class Inheritance
^^^^^^^^^^^^^^^^^

Theme can be created in multiple ways and each offers different starting point
for theme creation.

**Theme that re-writes all templates and static sources**

.. code-block:: python

    class MyThemeTheme(Theme):
        ...

**Theme that uses other theme functionality**

.. code-block:: python

    class MyTheme(ClassicGrayTheme):
        ...

.. topic:: Note

    This theme uses the functionality of another theme or overrides
    some of the templates, static sources, or such from inherited   template.


**Theme that uses uses other theme functionality but not templates**

.. code-block:: python

    class MyTheme(ClassicGrayTheme):
        default_template_dir = "path/to/templatedir"

.. topic:: Note

    This method is handy if you want the functionality of some theme and
    want to use a certain template set with that, for example when your
    theme addon actually offers multiple themes.

Terminology
^^^^^^^^^^^

**Base theme:** ``ClassicGrayTheme`` found in ``shuup/themes/classic_gray/theme.py``.

Templates
^^^^^^^^^

Overriding templates are pretty straight forward,
you have two use cases when overriding shuup templates.

**Case A**, overriding shuup front template:

So the base theme is satisfying, however you are not happy on the
category page. You can find the current category template
from ``shuup/front/templates/shuup/front/product/category.jinja``.

You can then copy said file to ``templates/mytheme/shuup/front/product/`` and make your changes.

**Case B**, overriding shuup front app template:

You want to make the search results page to reflect the changes made in
category page. In this case you must override
the file found in ``shuup/front/apps/simple_search/templates/shuup/simple_search/search_form.jinja``.

You can again copy that file to ``templates/mytheme/simple_search/search_form.jinja`` and make your changes.

Macros
^^^^^^

As said before, macros can be found
from ``shuup/front/templates/shuup/front/macros``. Under this folder is a
folder called ``theme``, this folder contains all the possible
theme specific macro override files.

In **Case A** in template example, you overrided the ``category.jinja``.
This file includes macro call: ``render_products_section()`` and you
want to change the way products are being rendered. In this case you
create a file in ``templates/mytheme/shuup/front/macros/theme/category.jinja``
and define the ``{% macro render_products_section() %}`` there
with the changes you want.

Some real life examples
^^^^^^^^^^^^^^^^^^^^^^^

Here are some real life examples based on using a theme inherited from ``ClassicGrayTheme``.

**I want the product boxes in category page look different.**

Add macro definition to ``templates/mytheme/shuup/front/macros/theme/product.jinja``.
Original definition can be found from ``shuup/front/templates/shuup/front/macros/product.jinja``

**I want to have a completely new theme with no base theme.**

Define your theme like this:

.. code-block:: python

    class MyTheme(Theme):
        template_dir = "mytheme"

Then add all template files to your template dir.
