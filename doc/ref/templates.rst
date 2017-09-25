Template Design
===============

This part of the documentation covers the structural elements of Shuup's default
templates and instructs you on how to create your own customized templates.

To be able to create customized templates you'll need to have understanding of the
principles of HTML and CSS.

If you would like to start creating your own customized templates with these
instructions you should already have a working Shuup installation with the
default frontend theme up and running. If not, you can start by reading
:doc:`Getting Started guide <../howto/getting_started_dev>`.

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
