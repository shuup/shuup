# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
"""
Patched version of Django's Makemessages that works with Jinja2.

Works by monkey patching django.utils.translation.trans_real.templatize
with our version.
"""
from io import BytesIO

import babel.messages.extract
from django.core.management.commands import makemessages
from django.utils.six import StringIO
from django.utils.translation import trans_real

KEYWORDS = dict(babel.messages.extract.DEFAULT_KEYWORDS, **{
    '_L': None,
    'gettext_lazy': None,
    'ugettext_lazy': None,
})

JINJA_EXTENSIONS = [
    'jinja2.ext.with_',
    'jinja2.ext.loopcontrols',
    'django_jinja.builtins.extensions.CsrfExtension',
    'shoop.xtheme.parsing.LayoutPartExtension',
    'shoop.xtheme.parsing.PlaceholderExtension',
    'shoop.xtheme.parsing.PluginExtension',
]

BABEL_OPTIONS = {
    'silent': 'false',
    'newstyle_gettext': 'on',
    'extensions': ','.join(JINJA_EXTENSIONS),
}

COMMENT_TAG = 'Translators:'


class Command(makemessages.Command):
    def handle(self, *args, **options):
        old_templatize = trans_real.templatize
        trans_real.templatize = jinja_messages_to_python
        try:
            super(Command, self).handle(*args, **options)
        finally:
            trans_real.templatize = old_templatize


def jinja_messages_to_python(src, origin=None):
    """
    Convert Jinja2 file to Python preserving only messages.
    """
    output = StringIO()
    output_lineno = 1
    for (lineno, message, comments, context) in extract_jinja(src, origin):
        for comment in comments:
            output.write(('# %s %s\n' % (COMMENT_TAG, comment)))
            output_lineno += 1
        lines_to_add = (lineno - output_lineno)
        if lines_to_add > 0:  # Try to keep line numbers in sync
            output.write(lines_to_add * '\n')
            output_lineno += lines_to_add
        output.write('gettext(%r),' % (message,))
    return output.getvalue()


def extract_jinja(contents, origin=None):
    return babel.messages.extract.extract(
        method='jinja2.ext.babel_extract',
        fileobj=BytesIO(contents.encode('utf-8')),
        options=BABEL_OPTIONS,
        keywords=KEYWORDS,
        comment_tags=(COMMENT_TAG,))
