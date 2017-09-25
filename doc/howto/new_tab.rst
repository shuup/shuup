Adding new tabs to admin views
==============================

Most views in admin support adding new tabs in admin
through :doc:`../ref/provides`.

.. note::
    To continue with this guide you should be familiar with the :doc:`addons`


Example: Adding a new category tab from addon
---------------------------------------------

As stated in :doc:`../ref/provides`, the ``admin_category_form_part`` provide
key can be used to add new tabs to the category view in admin.

Let's say we want to create an addon named **Category Addon**
that sets ``Category::status`` to ``CategoryStatus.INVISIBLE``
if the checkbox has been clicked. Makes sense right...


Form
^^^^

First, we have to create a simple ``Form`` for the field.

.. code-block:: python

    class AutomationForm(forms.Form):
        force_invisible = forms.BooleanField(label="Force invisible", default=False)


FormPart
^^^^^^^^

Then, we need a ``FormPart`` that will render the form within a given template.

.. code-block:: python

    class AutomationForm(forms.Form):
        force_invisible = forms.BooleanField(label="Force invisible", default=False)


    class CategoryFormPart(FormPart):
        priority = 9
        name = "category_example_form"
        form = AutomationForm

        def get_form_defs(self):
            if not self.object.pk:
                return

            yield TemplatedFormDef(
                name=self.name,
                form_class=self.form,
                template_name="shuup/autoform/admin/autoform.jinja",
                required=False
            )

        def form_valid(self, form):
            if self.name in form.forms:
                if form[self.name].cleaned_data.get("force_invisible", False):
                    self.object.status = CategoryStatus.INVISIBLE

.. note:: See :doc:`../ref/formpart` for more information.

The Template
^^^^^^^^^^^^

Now, lets add our template into our addons template folder
defined in the ``CategoryFormPart``: ``shuup/autoform/admin/autoform.jinja``

.. code-block:: html

    {% from "shuup/admin/macros/general.jinja" import content_block %}
    {% set magic_form = form["category_example_form"] %}

    {% call content_block(_("Force"), icon="fa-magic") %}
        {{ bs3.render(magic_form) }}
    {% endcall %}


The AppConfig
^^^^^^^^^^^^^

Next, we'll add the ``admin_category_form_part`` definition to your provides
(``"category_tab_example.admin_module.form_parts.CategoryFormPart"``).

.. code-block:: python

    from shuup.apps import AppConfig

    class CategoryAddonAppConfig(AppConfig):
        name = "category_addon"
        verbose_name = "Category Addon"
        label = "category_addon"

        provides = {
            "admin_category_form_part": [
                "category_tab_example.admin_module.form_parts.CategoryFormPart"
            ],
            ...
        }


Wrapping it all up
^^^^^^^^^^^^^^^^^^

Adding new tabs to the admin is a simple and effective
way of extending the functionality of your Shuup.

Tabs consist of three different items:

* ``Form``: you need a form to add functionality
* ``FormSet``: the "glue" between the ``Form`` and the template
* the template for the form which shows the merchant what you are up to.

You can visit :doc:`../ref/provides` to see which views are supported.


