Themes and Macros
=================

Themes and macros offer Shuup the extensibility of custom front layouts.

Themes are basically :doc:`Addons <addons>` that offer theme using :doc:`provides <provides>`.

There are however few theme specific things that are being addressed here.
While this document might include duplicate information
from :doc:`Template Design <templates>`, it's done to avoid hopping from document to another.

This document is a good starting point for first-time theme creators.

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
    Contains all your theme related files.

``theme_folder/locale``
    Contains all translation files. You can collect translations by
    running ``python -m shuup_workbench shuup_makemessages -l en``.

``theme_folder/plugins``
    Contains all the plugins your theme provides.
    Please note that plugins are available for this
    theme only if declared with ``MyTheme.plugins``.
    If you want to have your plugins in global plugin pool,
    your ``AppConfig`` should offer them with ``xtheme_plugin`` provide.

``theme_folder/templates`` ::
    Should match the ``template_dir`` set in your theme.
    This folder contains all the templates your theme offers.

``theme_folder/templates/plugins``
    Is a good place to store your plugins' templates.

``theme_folder/templates/shuup``
    Contains all the templates you wish to override from shuup.
    To override a category template you should have the
    file ``theme_folder/shuup/front/product/category.jinja`` in place.

    **Note** that ``theme_folder/shuup/front/index.jinja`` is a required file to have.
    Without this file the theme won't activate in front.

``theme_folder/templates/shuup/front/macros/theme``
    A folder where you can add macro overrides.

``theme_folder/static``
    Contains all the static files used by your templates.

Files
~~~~~

``theme_folder/__init__.py``
    Contains usually only one line which defines the location
    of the ``AppConfig``: ``default_app_config = __name__ + ".apps.AppConfig"``.

``theme_folder/apps.py``
    This file contains the ``AppConfig`` for your theme. ``AppConfig``
    can be defined like this ``class AppConfig(shuup.apps.AppConfig):``.
    More details about Django AppConfig can be found in `Django Documentation <https://docs.djangoproject.com/en/1.8/ref/applications/>`_.
    The ``AppConfig`` you defined also tells Shuup that the Addon is providing a theme.
    More about provides can be read from :doc:`Provides Documentation <provides>`.

``theme_folder/theme.py``
    This file contains the actual theme definition.
    Theme can be defined in several ways which are explained in :ref:`defining-theme`

.. _defining-theme:

Defining a Theme
----------------

As mentioned before, there are several ways to define a theme:

Theme that re-writes all templates and static sources
    This kind of theme should be defined: ``class MyTheme(Theme)``

A theme that uses the functionality of another theme
    This kind of theme can overwrite templates, static sources, or such from the parent theme.
    Should be defined: ``class MyTheme(ClassicGrayTheme)``

A theme that wants to get it's templates from totally different place
    Theme of this kind can be defined

    .. code-block:: python

        class MyTheme(ClassicGrayTheme):
            default_template_dir = "path/to/templatedir

    .. note:: This is handy if you want the functionality of some theme
              and want to use a certain template set with that, for
              example when your theme addon actually offers multiple themes.

Overriding templates and macros
-------------------------------

The general ideology with overriding templates and themes:

* Macros: simple block changes
* Templates: totally different structure

Most of the Shuup Front templates are found in ``shuup/front/templates/shuup/front/``
and macros in ``shuup/front/templates/shuup/front/macros``.

Shuup has some applications for front also, these are found in ``shuup/front/apps``.
These apps define their own templates and are not found
in the ``shuup/front/templates/shuup/front/``.

For the purposes of the following examples, we expect that your theme is defined like this

.. code-block:: python

    class MyTheme(ClassicGrayTheme):
        template_dir = "mytheme"

.. note:: Using this in real life you can use any theme as parent.

This means that your templates are found in ``templates/mytheme/shuup/``.

When referred to `Base theme` we are meaning ``ClassicGrayTheme`` found in ``shuup/themes/classic_gray/theme.py``.

.. note:: ``templates/mytheme/shuup/front/index.jinja`` must exist or the theme won't be activated.

Templates
~~~~~~~~~

Overriding templates are pretty straight forward,
you have two use cases when overriding Shuup templates.

**Case A**
    *Overriding Shuup front template*

    So the base theme is satisfying, however you are not happy on the
    category page. You can find the current category template
    from ``shuup/front/templates/shuup/front/product/category.jinja``.

    You can then copy said file to ``templates/mytheme/shuup/front/product/`` and make your changes.

**Case B**,
    *Overriding a Shuup front app template*

    You want to make the search results page to reflect the changes made in
    category page. In this case you must override the file found in
    ``shuup/front/apps/simple_search/templates/shuup/simple_search/search_form.jinja``.

    You can again copy that file to ``templates/mytheme/simple_search/search_form.jinja`` and make your changes.

Macros
~~~~~~

As said before, the original macro definitions used by Shuup base theme can be
found from ``shuup/front/templates/shuup/front/macros``. Inside this folder
you can find a folder called ``theme`` which contains the files used in
theme specific overwrites.

In **Case A** of the template example, you overwrited the ``category.jinja``.
This file includes several macro calls, including ``render_products_section()``.
Your goal is change the way products are being rendered. In this case you
create a file in ``templates/mytheme/shuup/front/macros/theme/category.jinja``
and define the ``{% macro render_products_section() %}`` there with the changes you want.

Simple real life examples
-------------------------

Here are some real life examples based on using a theme inherited from ``ClassicGrayTheme``.

**I want the product boxes in category page look different.**
    Add macro definition to ``templates/mytheme/shuup/front/macros/theme/product.jinja``.

    Original definition can be found from ``shuup/front/templates/shuup/front/macros/product.jinja``.

**I want to have a new theme with no base theme.**
    Define your theme like this:

    .. code-block:: python

        class MyTheme(Theme):
            template_dir = "mytheme"

    .. note:: Remember to add your template files in ``mytheme`` folder.
