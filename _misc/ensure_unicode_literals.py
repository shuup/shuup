# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import re
import os
import click
from ast import parse, NodeVisitor
from six import text_type

encoding_comment_regexp = re.compile(r'^#.+coding[=:]\s*([-\w.]+).+$', re.MULTILINE | re.I)


class StringVisitor(NodeVisitor):
    def __init__(self):
        self.texts = set()

    def visit_Str(self, node):  # noqa (N802)
        s = text_type(node.s)
        if ("\n" in s or s.islower() or s.isupper()):  # Looks like a constant or docstring
            return
        if " " in s.strip():  # Has spaces, that's texty
            if "%" in s or not all(32 <= ord(c) < 127 for c in s):  # Has a formatting character or is non-ascii
                self.texts.add(s)
        self.generic_visit(node)


def process_file(path):
    with open(path, "rb") as fp:
        source = fp.read()
    if b"unicode_literals" in source:
        return
    tree = parse(source, path)
    sv = StringVisitor()
    sv.visit(tree)
    return sv.texts


def fix_file(path):
    with open(path, "rb") as fp:
        source = fp.read().decode("utf-8")
        source_lines = source.splitlines()

    need_encoding_comment = any(ord(c) > 127 for c in source)
    first_non_comment_line_index = 0
    for line_index, line in enumerate(source_lines):
        if not line.strip():
            continue
        if encoding_comment_regexp.match(line):
            need_encoding_comment = False
        if not line.startswith("#"):
            first_non_comment_line_index = line_index
            break

    if "from __future__ import unicode_literals" not in source:
        source_lines.insert(first_non_comment_line_index, "from __future__ import unicode_literals")

    source = "\n".join(source_lines)
    if need_encoding_comment:
        source = "# -*- coding: utf-8 -*-\n" + source

    with open(path, "wb") as fp:
        fp.write(source.encode("utf-8"))
        fp.write(b"\n")


def gather_files(dirnames, filenames):
    files_to_process = []
    files_to_process.extend(filename for filename in filenames if filename.endswith(".py"))
    if dirnames:
        for dirname in dirnames:
            for path, dirnames, filenames in os.walk(dirname):
                for filename in filenames:
                    if filename.endswith(".py"):
                        files_to_process.append(os.path.join(path, filename))
    return files_to_process


@click.command()
@click.option("-f", "--file", "filenames", type=click.Path(exists=True, dir_okay=False), multiple=True)
@click.option("-d", "--dir", "dirnames", type=click.Path(exists=True, file_okay=False), multiple=True)
@click.option('--fix/--no-fix', default=False)
def command(filenames, dirnames, fix):
    for filename in gather_files(dirnames, filenames):
        results = process_file(filename)
        if results:
            print("%s: %d text-like strings but no unicode_literals" % (filename, len(results)))
            if fix:
                print("Fixing: %s" % filename)
                fix_file(filename)


if __name__ == "__main__":
    command()
