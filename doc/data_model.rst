Data model
==========

Data in Shoop is stored into database using regular :mod:`Django models
<django.db.models>` and it is accessed with Django's normal :ref:`query
API <retrieving-objects>`.  See :mod:`shoop.core.models` for list of
models in :term:`Shoop Core`.

Extending models
----------------

Non-polymorphic models
^^^^^^^^^^^^^^^^^^^^^^

Basic models (like :class:`~shoop.core.models.Product`,
:class:`~shoop.core.models.Category` or
:class:`~shoop.core.models.Order`) cannot be replaced.  To extend them,
create a new model for your extensions and link that to the original
model with a :class:`~django.db.models.OneToOneField`.

For example:

.. code-block:: python

   from django.core import models
   from shoop.core import models as shoop_models

   class MyProduct(models.Model):
       product = models.OneToOneField(shoop_models.Product)

       # fields of the extension...
       my_field = models.CharField(max_length=10)
       ...

.. TODO:: Check :ref:`multi-table-inheritance` for extending models

.. note::

   Even though basic models cannot be replaced, it is possible to
   replace the :class:`~django.contrib.auth.models.User` model. See
   :ref:`specifying-custom-user-model`.

Polymorphic models
^^^^^^^^^^^^^^^^^^

Polymorphic models (like :class:`~shoop.core.models.Contact`) can be
extended by inheritance.  The polymorphic base class has a :obj:`model
manager <django.db.models.Manager>` that makes sure that the returned
objects are correct type.  For example, when getting all
:class:`Contacts <shoop.core.models.Contact>` with a query like
``Contact.objects.all()``, the returned
:class:`~django.db.models.query.QuerySet` may have instances of
:class:`~shoop.core.models.PersonContact`,
:class:`~shoop.core.models.CompanyContact` and your custom class.

See `django-polymorphic's documentation
<http://django-polymorphic.readthedocs.org>`_ for details.
