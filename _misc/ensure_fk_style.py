# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import print_function

import sys
from ast import parse

import click
from sanity_utils import dotify_ast_name, find_files, XNodeVisitor


class ForeignKeyVisitor(XNodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_Call(self, node, parents):  # noqa (N802)
        name = dotify_ast_name(node.func)
        if any(name.endswith(suffix) for suffix in ("ForeignKey", "FilerFileField", "FilerImageField")):
            kwmap = dict((kw.arg, kw.value) for kw in node.keywords)
            if "on_delete" not in kwmap:
                self.errors.append("%d: %s call missing explicit `on_delete`" % (node.lineno, name))


def process_file(path):
    fkv = ForeignKeyVisitor()
    with open(path, "rb") as fp:
        source = fp.read()
    fkv.visit(parse(source, path))
    return fkv.errors


@click.command()
@click.option("-f", "--file", "filenames", type=click.Path(exists=True, dir_okay=False), multiple=True)
@click.option("-d", "--dir", "dirnames", type=click.Path(exists=True, file_okay=False), multiple=True)
def command(filenames, dirnames):
    for filename in find_files(dirnames, allowed_extensions=(".py",)):
        for error in process_file(filename):
            print("%s: %s" % (filename, error), file=sys.stderr)


if __name__ == "__main__":
    command()
