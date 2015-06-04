#!/usr/bin/env python3
"""
License header updater.
"""
from __future__ import unicode_literals

import os

HEADER = """
This file is part of Shoop.

Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.

This source code is licensed under the AGPLv3 license found in the
LICENSE file in the root directory of this source tree.
""".strip()

PY_HEADER = '\n'.join(('# ' + line).strip() for line in HEADER.splitlines())
JS_HEADER = (
    '/**\n' +
    '\n'.join((' * ' + line).strip() for line in HEADER.splitlines()) +
    '\n */')

PY_HEADER_LINES = PY_HEADER.encode('utf-8').splitlines()
JS_HEADER_LINES = JS_HEADER.encode('utf-8').splitlines()


def main():
    adders = [
        ('.py', add_header_to_python_file),
        ('.js', add_header_to_javascript_file),
    ]
    for (ext, adder) in adders:
        for path in find_files(ext):
            if os.stat(path).st_size == 0:
                print('%s: OK (Empty)' % (path,))
            elif not has_header(path):
                adder(path)
                print('%s: Modified' % (path,))
            else:
                print('%s: OK' % (path,))


def find_files(extension):
    for (path, dirnames, filenames) in os.walk('.'):
        for filename in filenames:
            if filename.endswith(extension):
                yield os.path.join(path, filename)


def has_header(path):
    with open(path, 'rb') as fp:
        return b"This file is part of Shoop." in fp.read(256)


def add_header_to_python_file(path):
    lines = get_lines(path)
    if lines:
        i = 0
        if lines[i].startswith(b'#!'):
            i += 1
        if i < len(lines) and b'coding' in lines[i]:
            i += 1

        new_lines = lines[:i] + PY_HEADER_LINES + lines[i:]
        write_lines(path, new_lines)


def add_header_to_javascript_file(path):
    lines = get_lines(path)
    if lines:
        new_lines = JS_HEADER_LINES + lines
        write_lines(path, new_lines)


def get_lines(path):
    with open(path, 'rb') as fp:
        contents = fp.read()
    if not contents.strip():
        return []
    return contents.splitlines()


def write_lines(path, new_lines):
    with open(path, 'wb') as fp:
        for line in new_lines:
            fp.write(line + b'\n')


if __name__ == '__main__':
    main()
