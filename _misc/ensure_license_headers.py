#!/usr/bin/env python3
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
License header updater.
"""
from __future__ import unicode_literals

import argparse
import os
import sanity_utils
import sys

HEADER = """
This file is part of Shuup.

Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.

This source code is licensed under the OSL-3.0 license found in the
LICENSE file in the root directory of this source tree.
""".strip()

PY_HEADER = "\n".join(("# " + line).strip() for line in HEADER.splitlines())
JS_HEADER = "/**\n" + "\n".join((" * " + line).rstrip() for line in HEADER.splitlines()) + "\n */"

PY_HEADER_LINES = PY_HEADER.encode("utf-8").splitlines()
JS_HEADER_LINES = JS_HEADER.encode("utf-8").splitlines()


def get_adders():
    return {".py": add_header_to_python_file, ".js": add_header_to_javascript_file}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="+", help="Directory roots to recurse through")
    ap.add_argument("-w", "--write", help="Actually write changes", action="store_true")
    ap.add_argument("-s", "--exit-status", help="Exit with error status when missing headers", action="store_true")
    ap.add_argument("-v", "--verbose", help="Log OK files too", action="store_true")
    args = ap.parse_args()
    adders = get_adders()
    paths = find_files(roots=args.root, extensions=set(adders.keys()))
    missing = process_files(paths, adders, verbose=args.verbose, write=args.write)
    if args.exit_status and missing:
        return 1
    return 0


def process_files(paths, adders, verbose, write):
    width = max(len(s) for s in paths)
    missing = set()
    for path in sorted(paths):
        if os.stat(path).st_size == 0:
            if verbose:
                print("[+]:%-*s: File is empty" % (width, path))  # noqa
        elif not has_header(path):
            missing.add(path)

            if write:
                adder = adders[os.path.splitext(path)[1]]
                adder(path)
                print("[!]:%-*s: Modified" % (width, path))  # noqa
            else:
                print("[!]:%-*s: Requires license header" % (width, path))  # noqa
        else:
            if verbose:
                print("[+]:%-*s: File has license header" % (width, path))  # noqa
    return missing


def find_files(roots, extensions):
    paths = set()
    generated_resources = set()
    for root in roots:
        for file in sanity_utils.find_files(
            root,
            generated_resources=generated_resources,
            allowed_extensions=extensions,
            ignored_dirs=sanity_utils.IGNORED_DIRS + ["migrations"],
        ):
            if not is_file_ignored(file):
                paths.add(file)
    paths -= generated_resources
    return paths


def is_file_ignored(filepath):
    filepath = filepath.replace(os.sep, "/")
    return ("vendor" in filepath) or ("doc/_ext/djangodocs.py" in filepath)


def has_header(path):
    with open(path, "rb") as fp:
        return b"This file is part of Shuup." in fp.read(256)


def add_header_to_python_file(path):
    lines = get_lines(path)
    if lines:
        i = 0
        if lines[i].startswith(b"#!"):
            i += 1
        if i < len(lines) and b"coding" in lines[i]:
            i += 1

        new_lines = lines[:i] + PY_HEADER_LINES + lines[i:]
        write_lines(path, new_lines)


def add_header_to_javascript_file(path):
    lines = get_lines(path)
    if lines:
        new_lines = JS_HEADER_LINES + lines
        write_lines(path, new_lines)


def get_lines(path):
    with open(path, "rb") as fp:
        contents = fp.read()
    if not contents.strip():
        return []
    return contents.splitlines()


def write_lines(path, new_lines):
    with open(path, "wb") as fp:
        for line in new_lines:
            fp.write(line + b"\n")


if __name__ == "__main__":
    sys.exit(main())
