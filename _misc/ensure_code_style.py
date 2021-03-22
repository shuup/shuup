# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import print_function

import ast
import click
import sys
from itertools import chain
from sanity_utils import IGNORED_DIRS, XNodeVisitor, dotify_ast_name, find_files, get_assign_first_target

KNOWN_ACRONYMS = ("SKU", "GTIN", "URL", "IP")


class ForeignKeyVisitor(XNodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_Call(self, node, parents):  # noqa (N802)
        name = dotify_ast_name(node.func)
        if any(name.endswith(suffix) for suffix in ("ForeignKey", "FilerFileField", "FilerImageField")):
            kwmap = dict((kw.arg, kw.value) for kw in node.keywords)
            if "on_delete" not in kwmap:
                self.errors.append("Error! %d: %s call missing explicit `on_delete`." % (node.lineno, name))


class VerboseNameVisitor(XNodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_Call(self, node, parents, context=None):  # noqa (N802)
        name = dotify_ast_name(node.func)
        if name == "InternalIdentifierField":
            return
        if name == "TranslatedFields":
            for kw in node.keywords:
                if isinstance(kw.value, ast.Call):
                    self.visit_Call(kw.value, parents, context=kw.arg)
            return
        if not any(name.endswith(suffix) for suffix in ("ForeignKey", "Field")):
            return

        if not context:
            if isinstance(parents[-1], ast.Assign):
                context = get_assign_first_target(parents[-1])

        if context and (context.startswith("_") or context.endswith("data")):
            return

        kwmap = dict((kw.arg, kw.value) for kw in node.keywords)

        kw_value = None
        needle = None
        for needle in ("verbose_name", "label"):
            kw_value = kwmap.get(needle)
            if kw_value:
                break
        if not kw_value:
            if node.kwargs:  # Assume dynamic use (has **kwargs)
                return
            self.errors.append(
                "Error! %d: %s call missing verbose_name or label (ctx: %s)." % (node.lineno, name, context)
            )
            return

        if isinstance(kw_value, ast.BinOp) and isinstance(kw_value.op, ast.Mod):
            # It's an interpolation operation; use the lvalue (probably the call)
            kw_value = kw_value.left

        if isinstance(kw_value, ast.Call) and dotify_ast_name(kw_value.func) == "_":
            arg = kw_value.args[0]
            if isinstance(arg, ast.Str) and needle == "verbose_name":
                if not arg.s[0].islower() and not any(arg.s.startswith(acronym) for acronym in KNOWN_ACRONYMS):
                    self.errors.append(
                        "Error! %d: %s `%s` not lower-case (value: %r) (ctx: %s)."
                        % (node.lineno, name, needle, arg.s, context)
                    )
            return

        if isinstance(kw_value, ast.Name):  # It's a variable
            return

        self.errors.append(
            "Error! %d: %s `%s` present but not translatable (ctx: %s)." % (node.lineno, name, needle, context)
        )


def process_file(path, checkers):
    with open(path, "rb") as fp:
        source = fp.read()
    for checker_class in checkers:
        ck = checker_class()
        ck.visit(ast.parse(source, path))
        for err in ck.errors:
            yield "%s: %s" % (checker_class.__name__, err)


def add_checker(ctx, param, value):
    ctx.params.setdefault("checkers", set()).add(param.name)


@click.command()
@click.option(
    "--fks", "ForeignKeyVisitor", help="check foreign keys", callback=add_checker, is_flag=True, expose_value=False
)
@click.option(
    "--vns", "VerboseNameVisitor", help="check verbose names", callback=add_checker, is_flag=True, expose_value=False
)
@click.option("-f", "--file", "filenames", type=click.Path(exists=True, dir_okay=False), multiple=True)
@click.option("-d", "--dir", "dirnames", type=click.Path(exists=True, file_okay=False), multiple=True)
@click.option("-g", "--group/--no-group")
def command(filenames, dirnames, checkers, group=False):
    error_count = 0
    all_filenames = chain(
        find_files(dirnames, allowed_extensions=(".py",), ignored_dirs=IGNORED_DIRS + ["migrations"]), filenames
    )
    checkers = [globals()[name] for name in checkers]
    for filename in all_filenames:
        file_errors = list(process_file(filename, checkers))
        if not file_errors:
            continue
        if group:
            print("%s:" % filename, file=sys.stderr)  # noqa
            for error in file_errors:
                print("    %s" % error, file=sys.stderr)  # noqa
                error_count += 1
            continue
        for error in file_errors:
            print("%s:%s" % (filename, error), file=sys.stderr)  # noqa
            error_count += 1

    print("###########################")  # noqa
    print("Total errors to handle: %d" % error_count)  # noqa
    print("###########################")  # noqa


if __name__ == "__main__":
    command()
