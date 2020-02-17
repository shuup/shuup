# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import re
import sys
import token
import tokenize

import django.conf
import six

import shuup.apps

FILE_READ_KWARGS = {"mode": "rb"}
if six.PY3:
    FILE_READ_KWARGS = {"mode": "r", "encoding": "utf-8"}

_TOKEN_MAP = dict(((k, v) for (v, k) in token.tok_name.items()))
COMMENT_TOKEN = _TOKEN_MAP['COMMENT']


def get_known_settings_documentation(order_by='app', only_changed=False):
    def orderer(setting):
        if order_by == 'app':
            return (setting['app_name'], setting['name'])
        elif order_by == 'name':
            return setting['name']

    known_settings = get_known_settings_with_comments()

    doc_items = []
    sorted_settings = sorted(known_settings, key=orderer)
    for setting in sorted_settings:
        default_value = setting['default']
        current_value = getattr(django.conf.settings, setting['name'])
        if only_changed and default_value == current_value:
            continue
        title = '{} (from {})'.format(setting['name'], setting['app_name'])
        doc = (setting['comment'] or 'Undocumented').strip()
        indented_doc = '\n    '.join(('    ' + doc).splitlines()).rstrip()
        default = '    Default value: {!r}'.format(default_value)
        current = '    Current value: {!r}'.format(current_value)
        blocks = [title, indented_doc, '', default, current]
        doc_items.append('\n'.join(blocks))
    return '\n\n'.join(doc_items)


def get_known_settings_with_comments():
    known_settings = shuup.apps.get_known_settings()

    comments = {}
    modules = [x.module for x in known_settings]
    for module in modules:
        names = set(x.name for x in known_settings if x.module == module)
        comments.update(_get_comments_before_assignments(module, names))

    def to_dict_with_comment(setting):
        return dict(vars(setting), comment=comments[setting.name])

    return [to_dict_with_comment(x) for x in known_settings]


def _get_comments_before_assignments(module_name, names):
    """
    Get comments before assign statements in Python module.

    Given module must have __file__ property that points to readable
    file.

    :return: mapping from name to comment string
    :rtype: dict[str,str]
    """
    module = sys.modules.get(module_name)
    module_pyc_file = getattr(module, '__file__', '')
    module_py_file = re.sub('.py[cdo]?$', '.py', module_pyc_file)
    if not os.path.exists(module_py_file):
        return {}

    with open(module_py_file, **FILE_READ_KWARGS) as fp:
        tokens = list(tokenize.generate_tokens(fp.readline))

    name_assign_tokens = [
        (tokens[i - 1][1], i - 1)  # (name, position)
        for (i, t) in enumerate(tokens)
        if i > 0 and t[0:2] == (token.OP, '=') and
        tokens[i - 1][0] == token.NAME and
        tokens[i - 1][1] in names]

    def get_comment_before(pos):
        p = pos
        while p >= 0 and tokens[p][0] != token.NEWLINE:
            p -= 1
        return '\n'.join(
            re.sub('^#: ?', '', x[1])
            for x in tokens[(p + 1):pos]
            if x[0] == COMMENT_TOKEN and x[1].startswith('#:'))

    return dict(
        (name, get_comment_before(pos))
        for (name, pos) in name_assign_tokens)
