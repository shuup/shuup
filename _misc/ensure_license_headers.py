#!/usr/bin/env python3
"""
License header updater.
"""
from __future__ import unicode_literals

import os
import argparse

HEADER = """
This file is part of Shoop.

Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.

This source code is licensed under the AGPLv3 license found in the
LICENSE file in the root directory of this source tree.
""".strip()

PY_HEADER = '\n'.join(('# ' + line).strip() for line in HEADER.splitlines())
JS_HEADER = (
    '/**\n' +
    '\n'.join((' * ' + line).rstrip() for line in HEADER.splitlines()) +
    '\n */')

PY_HEADER_LINES = PY_HEADER.encode('utf-8').splitlines()
JS_HEADER_LINES = JS_HEADER.encode('utf-8').splitlines()


def get_adders():
    return {
        '.py': add_header_to_python_file,
        '.js': add_header_to_javascript_file
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="+", help="Directory roots to recurse through")
    ap.add_argument("-w", "--write", help="Actually write changes", action="store_true")
    ap.add_argument("-v", "--verbose", help="Log OK files too", action="store_true")
    args = ap.parse_args()
    paths = set()
    adders = get_adders()
    extensions = set(adders.keys())
    for root in args.root:
        paths |= set(find_files(root, extensions))

    width = max(len(s) for s in paths)

    for path in sorted(paths):
        if os.stat(path).st_size == 0:
            if args.verbose:
                print('[+]:%-*s: File is empty' % (width, path))
        elif not has_header(path):
            if args.write:
                adder = adders[os.path.splitext(path)[1]]
                adder(path)
                print('[!]:%-*s: Modified' % (width, path))
            else:
                print('[!]:%-*s: Requires license header' % (width, path))
        else:
            if args.verbose:
                print('[+]:%-*s: File has license header' % (width, path))


def find_files(root, extensions):
    for (path, dirnames, filenames) in os.walk(root):
        dirnames[:] = [
            dirname for dirname in dirnames if not is_file_ignored(os.path.join(path, dirname))
            ]
        for filename in filenames:
            if any(filename.endswith(extension) for extension in extensions):
                filepath = os.path.join(path, filename)
                if not is_file_ignored(filepath):
                    yield filepath


def is_file_ignored(filepath):
    filepath = filepath.replace(os.sep, "/")
    return (
        ('.git' in filepath) or
        ('venv' in filepath) or
        ('__pycache__' in filepath) or
        ('vendor' in filepath) or
        ('node_modules' in filepath) or
        ('bower_components' in filepath) or
        ('doc/_ext/djangodocs.py' in filepath)
    )


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
