Development Tools
=================

Sanity Checker
--------------

The ``check_sanity.py`` tool does basic text file sanity checking on the
codebase.

.. code-block::  shell

   python _misc/check_sanity.py

DocCov
------

The ``doccov.py`` tool checks for docstring coverage and docstring style.

.. code-block::  shell

   python _misc/doccov.py -o report.html shuup


Ensure Code Style
-----------------

The ``ensure_code_style.py`` tool has a couple checkers:

* one that checks that all ``ForeignKey``s are declared with
  ``on_delete`` clauses
* one that checks that model and form fields have properly translatable
  verbose names

.. code-block::  shell

   python _misc/ensure_code_style.py shuup

You also need to make sure to run isort, black and flake8 to check
the code style and to search for issues in your code.

.. code-block::  shell

   flake8 .
   isort --check --diff .
   black --check --diff .

Ensure License Headers
----------------------

The ``ensure_license_headers.py`` tool checks that all source files have the requisite
license header.  It can also optionally write the headers to the files by itself.

.. code-block::  shell

   python _misc/ensure_license_headers.py shuup
   # or to write changes:
   python _misc/ensure_license_headers.py -w shuup


Ensure Unicode Literals
-----------------------

The ``ensure_unicode_literals.py`` tool checks that all Python files have the
``from __future import unicode_literals`` statement, to improve Python 2 compatibility.

It can also optionally add these statements itself.

.. code-block::  shell

   python _misc/ensure_unicode_literals.py shuup
   # or to write changes:
   python _misc/ensure_unicode_literals.py -w shuup
