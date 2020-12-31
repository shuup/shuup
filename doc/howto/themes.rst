Themes and Macros
=================

The look and feel of your Shuup storefront can be completely customized to fit your
brand using custom themes and macros.

In Shuup lingo, themes are :doc:`addons <addons>` that customize the look and
feel of a storefront using ``xtheme`` :doc:`provides <../ref/provides>`.

This document is a good starting point for first-time theme creators. Please refer to Classic Gray, the theme provided
by Shuup base, as an example. This theme can be found in `shuup/themes/classic_gray`.

Theme Structure
---------------

.. code-block:: none

    theme_folder
        locale
        plugins
            __init__.py
        templates
            theme_name
                plugins
                shuup
        static
        __init__.py
        apps.py
        theme.py

..


Folders
~~~~~~~

``theme_folder``
    Contains all your theme-related files.

``theme_folder/locale``
    Contains all translation files. You can collect translations by
    running ``python -m shuup_workbench shuup_makemessages -l en``.

``theme_folder/plugins``
    Contains all the plugins provided by your theme.
    Theme-specific plugins should be declared in ``MyTheme.plugins``.
    If you want to have your plugins available for any theme,
    your ``AppConfig`` should offer them with the ``xtheme_plugin`` provide.

``theme_folder/templates``
    Contains your theme templates. Should match the ``template_dir`` set in your ``Theme`` class.

``theme_folder/templates/plugins``
    Contains your plugins' templates.

``theme_folder/templates/shuup``
    Contains all templates overrides.
    **Note** that ``theme_folder/shuup/front/index.jinja`` is a required file.

``theme_folder/templates/shuup/front/macros/theme``
    Contains macro overrides.

``theme_folder/static``
    Contains all the static files used by your templates.

Files
~~~~~

``theme_folder/__init__.py``
    Usually contains only one line which defines the location
    of the ``AppConfig``: ``default_app_config = __name__ + ".apps.AppConfig"``.

``theme_folder/apps.py``
    This file contains the ``AppConfig`` for your theme. The ``AppConfig`` is the mechanism by which Shuup recognizes
    that the addon is providing a theme.
    More details about Django AppConfig can be found in `Django Documentation <https://docs.djangoproject.com/en/1.8/ref/applications/>`_.
    More about provides can be found in :doc:`Provides Documentation <../ref/provides>`.

``theme_folder/theme.py``
    Contains the actual theme definition.
    See :ref:`defining-theme`

.. _defining-theme:

Defining a Theme
----------------

Themes are defined in ``theme_folder/theme.py``.

To create a brand new theme with completely new templates and static resources, extend ``Theme``.

To create a theme which uses the functionality of another theme (to override templates and static resources, for example),
simply extend that theme: ``class MyTheme(SomeOtherTheme):``


Overriding Templates and Macros
-------------------------------

Generally, templates are used to define overall page layout whereas macros define component structure (ie. the product
boxes shown on the category page).

Most of the Shuup front templates are found in ``shuup/front/templates/shuup/front/``
and macros in ``shuup/front/templates/shuup/front/macros/``.

Additionally, Shuup has some applications for front (found in ``shuup/front/apps``).
These apps define their own templates in
in ``shuup/front/apps/<appname>/templates/``.


Templates
~~~~~~~~~

Lets walk through two typical use cases you may encounter when overriding Shuup templates.

For the purposes of the following examples, your theme should be defined as follows:

.. code-block:: python

    class MyTheme(ClassicGrayTheme):
        template_dir = "mytheme"  # your templates should be in templates/mytheme/shuup/

.. note:: In a real project, you can use any ``Theme`` as the parent.

.. note:: ``templates/mytheme/shuup/front/index.jinja`` must exist for the theme to work.


**Case A**
    *Overriding a Shuup front template*

    So the classic gray theme is satisfying, but you are not happy with the
    category page. You can find the current category template
    in ``shuup/front/templates/shuup/front/product/category.jinja``.

    You can then copy said file to ``templates/mytheme/shuup/front/product/`` and make your changes.

**Case B**,
    *Overriding a Shuup front app template*

    You want to make the search results page reflect the changes made on the
    category page. In this case, you need to override the file found in
    ``shuup/front/apps/simple_search/templates/shuup/simple_search/search_form.jinja``.

    You can again copy that file to ``templates/mytheme/simple_search/search_form.jinja`` and make your changes.

Macros
~~~~~~

The original macro definitions used by Shuup base theme can be
found in ``shuup/front/templates/shuup/front/macros``. Inside this folder,
you can find a folder called ``theme`` which contains the files used for
theme-specific overrides.

In **Case A** of the template example, you overwrote ``category.jinja``.
This file includes several macro calls, including ``render_products_section()``.
Your goal is change the way products are being rendered. In this case, you can
create ``templates/mytheme/shuup/front/macros/theme/category.jinja``
and define the ``{% macro render_products_section() %}`` there with the changes you want.


Styles
------

Theme can define multiple stylesheets. This allows theme designers to use the
same base ``.less`` and simply overwrite colors or make other small stylistic changes.

See ``shuup/themes/classic_gray/`` for examples on how to define multiple stylesheets and
``shuup/front/templates/shuup/front/base.jinja`` for how to use them in your own `base.jinja`

These styles can then be selected by the merchant via Admin -> Storefront -> Themes -> configure.


General Information
-------------------

Shuup themes support our xtheme template engine which offers custom
functionality on top of the common Jinja2 templates.


Placeholders
~~~~~~~~~~~~

Theme designers can add placeholders to their themes. These placeholders
then function as a place for the merchant to add content from plugins.


A placeholder can be defined as easy as:

.. code-block:: html

  {% placeholder "my_placeholder" %}{% endplaceholder %}

.. note::

  You can have multiple placeholders with the same name in the same page.
  This functionality is important when you must have the same content block
  to look different in different view sizes.

The placeholder can also be global:

.. code-block:: html

  {% placeholder "my_placeholder" global %}{% endplaceholder %}

.. note::

  This kind of placeholder is good for footers where the
  content isn't attached to a single page.

A placeholder can have default content, which can then be overridden
by the merchant. In the following example, the theme creator has
created a placeholder where there is a text plugin by default.
This text plugin has then default text "My example text".

.. code-block:: html

  {% placeholder "my_placeholder" %}
      {% plugin "text" %}
          text = "My example text"
      {% endplugin %}
  {% endplaceholder %}

.. note::

  Using default content is important to make your theme to look
  good out of the box. Just make sure the plugins you use are usable with
  your theme even with very basic Shuup installation. If you are unsure,
  provide these plugins as a part of your theme distribution.

.. note::
  All placeholder content is cached to keep the rendering efficient. This
  means that content got from outside the plugin context needs to be
  either fetched asynchronously (like product content) or you need to
  make sure xtheme cache is bumped when your models affecting the
  plugin content is changed (for example see simple_cms app config).
