# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import argparse
import ast
import jinja2
import linecache
import logging
import os
import re
import sys
from collections import Counter
from django.utils.text import slugify
from sanity_utils import find_files

_paragraph_re = re.compile(r"(?:\r\n|\r|\n){2,}")


@jinja2.evalcontextfilter
def nl2br(eval_ctx, value):
    result = u"\n\n".join(u"<p>%s</p>" % p.replace("\n", "<br>\n") for p in _paragraph_re.split(jinja2.escape(value)))
    if eval_ctx.autoescape:
        result = jinja2.Markup(result)
    return result


REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<body>
<div class="container">

<h1>DocCov Report</h1>
<div class="progress">
  <div class="progress-bar" role="progressbar" style="width: {{ percentage }}%;">
    {{ percentage }}% ({{ grand_totals.n_documented }}/{{ grand_totals.n_total }})
  </div>
</div>
<hr>
<table class="table table-striped table-condensed">
<tr>
    <th>Filename</th>
    <th>Documented</th>
    <th>Undocumented</th>
    <th>Total</th>
    <th colspan="2">Percentage documented</th>
</tr>
{% for file in files_by_percentage %}
<tr>
    <td><a href="#{{ file.id }}">{{ file.path }}</a></td>
    <td class="text-right">{{ file.totals.n_documented }}</td>
    <td class="text-right">{{ file.totals.n_undocumented }}</td>
    <td class="text-right">{{ file.totals.n_total }}</td>
    <td class="text-right">{{ file.percentage }}%</td>
    <td width=50%>
        <div
          class="progress-bar" role="progressbar"
          style="width: {{ file.percentage }}%;"
        ><span>{{ file.percentage }}%</span></div>
    </td>
</tr>
{% endfor %}
</table>
{% for file in files %}
<h2 id="{{ file.id }}">{{ file.path }}</h2>
<div class="progress">
  <div class="progress-bar" role="progressbar" style="width: {{ file.percentage }}%;">
    {{ file.percentage }}% ({{ file.totals.n_documented }}/{{ file.totals.n_total }})
  </div>
</div>
<table class="table table-striped">
<tr>
    <th>Line</th>
    <th>Object</th>
    <th>Docstring</th>
    <th>Errors</th>
</tr>
{% for m in file.object_stats %}
<tr class="bg-{{ m.klass }}">
    <td class="text-right">{{ m.line }}</td>
    <td>{{ m.obj }}</td>
    {% if m.docinfo %}
    <td>{{ m.docinfo.docstring|nl2br }}</td>
    <td>
        {% set ve = m.docinfo.validation_errors|sort %}
        {% if ve %}
        <ul>{% for e in ve %}<li>{{ e }}</li>{% endfor %}</ul>
        {% endif %}
    </td>
    {% else %}
    <td colspan="2"><i>Not documented</i></td>
    {% endif %}
</tr>
{% endfor %}
</table>
{% endfor %}
</div>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootswatch/3.3.0/journal/bootstrap.min.css">
<style>.bg-success{background: #dff0d8 !important}</style>
</body>
</html>
""".strip()

IGNORED_FUNCTIONS = set(
    [
        "__abs__",
        "__add__",
        "__all__",
        "__and__",
        "__builtins__",
        "__cached__",
        "__concat__",
        "__contains__",
        "__delitem__",
        "__doc__",
        "__eq__",
        "__file__",
        "__floordiv__",
        "__ge__",
        "__getitem__",
        "__gt__",
        "__iadd__",
        "__iand__",
        "__iconcat__",
        "__ifloordiv__",
        "__ilshift__",
        "__imod__",
        "__imul__",
        "__index__",
        "__inv__",
        "__invert__",
        "__ior__",
        "__ipow__",
        "__irshift__",
        "__isub__",
        "__itruediv__",
        "__ixor__",
        "__le__",
        "__loader__",
        "__lshift__",
        "__lt__",
        "__mod__",
        "__mul__",
        "__name__",
        "__ne__",
        "__neg__",
        "__not__",
        "__or__",
        "__package__",
        "__pos__",
        "__pow__",
        "__rshift__",
        "__setitem__",
        "__spec__",
        "__sub__",
        "__truediv__",
        "__xor__",
        # The usual suspects
        "__str__",
        "__repr__",
        # CBV generics:
        "dispatch",
        "form_invalid",
        "form_valid",
        "get",
        "get_context_data",
        "get_form",
        "get_form_class",
        "get_form_kwargs",
        "get_object",
        "get_success_url",
        "post",
    ]
)

IGNORED_CLASSES = set(
    [
        "Labels",
        "Meta",
    ]
)

IGNORED_FIRST_ARGS = set(["self", "cls"])  # classmethods

IGNORED_ARGS = set([])

ARG_RE = re.compile(r":param\s+([a-z_0-9]+)", re.I)

INTERNAL_NAME_RE = re.compile("^_[^_].+$")

DOCCOV_DIRECTIVE_COMMENT_RE = re.compile(r"doccov:\s*(.+)", re.I)


class ReturnValueVisitor(ast.NodeVisitor):
    def __init__(self):
        self.returned_values = set()

    @property
    def has_valueful_return(self):
        return bool(self.returned_values)

    def visit_Return(self, node):  # noqa (N802)
        retval = node.value
        if retval:
            self.returned_values.add(retval)


class Validator(object):
    disabling_directives = []

    def validate(self, docinfo):
        pass


class GenericDocstringValidator(Validator):
    def validate(self, docinfo):
        docstring = docinfo.docstring
        if docstring:
            if len(docstring) < 15:
                yield "Error! Docstring is too short."
            sep = ".\n" if "\n" in docstring else "."
            if sep not in docstring:
                yield "Error! Docstring doesn't seem to have an opening sentence."
        else:
            if not self.can_elide_docstring(docinfo):
                yield "Error! Docstring is missing."

    def can_elide_docstring(self, docinfo):
        if docinfo.name == "__init__" and not docinfo.required_args:
            return True
        return False


class ArgValidator(Validator):
    disabling_directives = ("noargs",)

    def validate(self, docinfo):
        for arg in sorted(docinfo.missing_args):
            yield u"Error! Missing mention of arg `%s`" % arg
        for arg in sorted(docinfo.extraneous_args):
            yield u"Error! Extraneous mention of arg `%s`" % arg


class ReturnValidator(Validator):
    disabling_directives = ("noreturn",)

    def validate(self, docinfo):
        node = docinfo.node
        docstring = docinfo.docstring
        if not isinstance(node, ast.FunctionDef):
            return
        rvv = ReturnValueVisitor()
        rvv.visit(node)
        if rvv.has_valueful_return:
            if not (":return" in docstring or ":rtype" in docstring):
                yield u"Error! Undocumented return value(s)"


class DocInfo(object):
    validator_classes = [GenericDocstringValidator, ArgValidator, ReturnValidator]

    def __init__(self, node, filename):
        self.node = node
        self.filename = filename
        self.directives = ""
        directive_match = DOCCOV_DIRECTIVE_COMMENT_RE.search(linecache.getline(filename, node.lineno))
        if directive_match:
            self.directives = directive_match.group(1).lower()
        self.name = getattr(node, "name", None) or ""
        self.docstring = (self.parse_docstring(node) or u"").strip()
        self.named_args = [a.arg for a in node.args.args] if hasattr(node, "args") else []
        if self.named_args and self.named_args[0] in IGNORED_FIRST_ARGS:
            self.named_args.pop(0)

        self.required_args = set(arg for arg in self.named_args if arg not in IGNORED_ARGS)
        self.mentioned_args = set(self.parse_arg_mentions(self.docstring))
        self.missing_args = self.required_args - self.mentioned_args
        self.extraneous_args = self.mentioned_args - self.required_args - set(["args", "kwargs"])
        self.validation_errors = list(self.validate())
        self.valid = not self.validation_errors

    def _prevalidate(self):
        if "migrations" in self.filename:  # Nothing in migration files is documentation-worthwhile
            return False
        if "ignore" in self.directives:
            return False
        if INTERNAL_NAME_RE.match(self.name):
            return False
        return True

    def validate(self):
        if not self._prevalidate():
            return

        for validator_class in self.validator_classes:
            validator = validator_class()
            if any((directive in self.directives) for directive in validator_class.disabling_directives):
                continue
            for error in validator.validate(self):
                yield error

    @staticmethod
    def parse_docstring(node):
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Str):
                value = node.body[0].value.s
                return value

    @staticmethod
    def parse_arg_mentions(docstring):
        return set(m.group(1) for m in ARG_RE.finditer(docstring))


class DocStringVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.objects = {}
        self._class_stack = []

    def _get_name(self, node):
        name = node.name
        if self._class_stack:
            name = "::".join([c.name for c in self._class_stack] + [name])
        line = node.lineno
        if isinstance(node, ast.FunctionDef):
            return (line, "func", name + "()")
        elif isinstance(node, ast.ClassDef):
            return (line, "class", name)
        else:
            raise NotImplementedError("Error! Not implemented: name for %s." % node)

    def visit_FunctionDef(self, node):  # noqa (N802)
        if node.name in IGNORED_FUNCTIONS:
            return
        self.objects[self._get_name(node)] = DocInfo(node, self.filename)

    def visit_ClassDef(self, node):  # noqa (N802)
        if node.name in IGNORED_CLASSES:
            return
        self.objects[self._get_name(node)] = DocInfo(node, self.filename)
        self._class_stack.append(node)
        self.generic_visit(node)
        self._class_stack.pop(-1)


class DocCov(object):
    def __init__(self):
        self.filenames = set()
        self.objects_by_file = {}
        self.log = logging.getLogger("DocCov")

    def check_files(self):
        for filename in sorted(self.filenames):
            self.check_file(filename)

    def check_file(self, filename):
        with open(filename, "rb") as inf:
            data = inf.read()
            try:
                tree = ast.parse(data, filename)
            except SyntaxError:
                self.log.exception("Error! Can't parse %s." % filename)
                return
        visitor = DocStringVisitor(filename=filename)
        visitor.visit(tree)
        self.objects_by_file[filename] = visitor.objects

    def add_root(self, path):
        path = os.path.realpath(path)
        if os.path.isdir(path):
            for filepath in find_files(path, allowed_extensions=(".py",)):
                if filepath.startswith("test_"):
                    self.log.info("Info! Skipping: %s" % filepath)
                    continue
                self.filenames.add(filepath)
        elif path.endswith(".py"):
            self.filenames.add(path)

    def write_report(self, output_file):
        template_file_list = []
        common_prefix = os.path.commonprefix(self.objects_by_file.keys())
        grand_totals = Counter()
        for path, objects in sorted(self.objects_by_file.items()):
            clean_path = path[len(common_prefix) :].replace(os.sep, "/")
            n_documented = sum([1 for m in objects.values() if m and m.valid])
            n_total = float(len(objects))
            n_undocumented = n_total - n_documented

            file_totals = Counter({"n_documented": n_documented, "n_total": n_total, "n_undocumented": n_undocumented})

            grand_totals += file_totals

            if n_total:
                object_stats = [
                    {
                        "type": type,
                        "line": line,
                        "obj": obj,
                        "klass": "success" if (docinfo and docinfo.valid) else "error",
                        "docinfo": docinfo,
                    }
                    for ((line, type, obj), docinfo) in sorted(objects.items())
                ]
                template_file_list.append(
                    {
                        "id": slugify(clean_path),
                        "path": clean_path,
                        "totals": file_totals,
                        "percentage": round(n_documented / float(n_total) * 100, 1),
                        "object_stats": object_stats,
                    }
                )

        env = jinja2.Environment()
        env.filters["nl2br"] = nl2br
        data = env.from_string(REPORT_TEMPLATE).render(
            {
                "percentage": round(grand_totals["n_documented"] / float(grand_totals["n_total"]) * 100, 2),
                "grand_totals": grand_totals,
                "files": template_file_list,
                "files_by_percentage": sorted(template_file_list, key=lambda f: (f["percentage"], f["id"])),
            }
        )

        output_file.write(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", dest="output", type=argparse.FileType("w", encoding="utf-8"), default=sys.stdout)
    ap.add_argument("-v", "--verbose", dest="verbose", action="store_true")
    ap.add_argument("-q", "--quiet", dest="quiet", action="store_true")
    ap.add_argument("roots", metavar="root", nargs="+")
    args = ap.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=9001)
    else:
        logging.basicConfig(level=logging.INFO)

    dc = DocCov()
    for root in args.roots:
        dc.add_root(root)
    dc.check_files()
    dc.write_report(args.output)


if __name__ == "__main__":
    main()
