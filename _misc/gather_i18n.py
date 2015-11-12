#!/usr/bin/env python3
from __future__ import unicode_literals

import argparse
import logging

from babel.messages import Catalog
from babel.messages.extract import extract
from babel.messages.pofile import write_po
from django.conf import settings

import sanity_utils

settings.configure(USE_I18N=True)

KEYWORDS = {
    '_': None,
    '_L': None,
    'dgettext': (2,),
    'dngettext': (2, 3),
    'gettext': None,
    'gettext_lazy': None,
    'N_': None,
    'ngettext': (1, 2),
    'ugettext': None,
    'ugettext_lazy': None,
    'ungettext': (1, 2),
}

MAPPING = [
    ('.jinja', 'jinja2.ext.babel_extract'),
    ('.js', 'javascript'),
    ('.py', 'python'),
    # If required, see https://github.com/EnTeQuAk/babeldjango/blob/master/babeldjango/extract.py:
    # ('.html', 'extract_django'),
]


def extract_from_file(filename):
    for pattern, method in MAPPING:
        if filename.endswith(pattern):
            with open(filename, "rb") as in_file:
                for lineno, message, comments, context in extract(method, in_file, keywords=KEYWORDS):
                    lineno = 0  # Avoid messy diffs
                    yield filename, lineno, message, comments
            break


def write_po_wrap(fh, catalog):
    write_po(fh, catalog, width=0, no_location=False, omit_header=True, sort_output=True, sort_by_file=True)


def main():
    logging.basicConfig(level=logging.INFO)
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="+", help="Directory roots to recurse through")
    args = ap.parse_args()
    logging.info("Searching for files...")
    filenames = list(sanity_utils.find_files(
        roots=args.root,
        ignored_dirs=sanity_utils.IGNORED_DIRS + ["migrations"],
        allowed_extensions=set(m[0] for m in MAPPING)
    ))
    logging.info("Found %d files. Extracting messages...", len(filenames))

    static_catalog = Catalog(charset="UTF-8")
    js_catalog = Catalog(charset="UTF-8")
    for filename in filenames:
        for filename, lineno, message, comments in extract_from_file(filename):
            catalog = (js_catalog if filename.endswith(".js") else static_catalog)
            catalog.add(message, None, [(filename, lineno)], auto_comments=comments)
    with open("shoop-static.pot", "wb") as outf:
        write_po_wrap(outf, static_catalog)
        logging.info("Wrote %d static messages to %s.", len(static_catalog), outf.name)
    with open("shoop-js.pot", "wb") as outf:
        write_po_wrap(outf, js_catalog)
        logging.info("Wrote %d JavaScript messages to %s.", len(js_catalog), outf.name)


if __name__ == "__main__":
    main()
