Development Tools
=================

Sanity Checker
--------------

The ``check_sanity.py`` tool does basic code sanity checking on the codebase.
This should be done before pushing.

.. code-block::  shell

   python _misc/check_sanity.py

DocCov
------

The ``doccov.py`` tool checks for docstring coverage and docstring style.

.. code-block::  shell

   python _misc/doccov.py -o report.html shoop


Ensure FK Style
---------------

The ``ensure_fk_style.py`` tool checks that all ``ForeignKey``s are declared
with ``on_delete`` clauses.

.. code-block::  shell

   python _misc/ensure_fk_style.py shoop


Ensure License Headers
----------------------

The ``ensure_license_headers.py`` tool checks that all source files have the requisite
license header.  It can also optionally write the headers to the files by itself.

.. code-block::  shell

   python _misc/ensure_license_headers.py shoop
   # or to write changes:
   python _misc/ensure_license_headers.py -w shoop


Ensure Unicode Literals
-----------------------

The ``ensure_unicode_literals.py`` tool checks that all Python files have the
``from __future import unicode_literals`` statement, to improve Python 2 compatibility.

It can also optionally add these statements itself.

.. code-block::  shell

   python _misc/ensure_unicode_literals.py shoop
   # or to write changes:
   python _misc/ensure_unicode_literals.py -w shoop
