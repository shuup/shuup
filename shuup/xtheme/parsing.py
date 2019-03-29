# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
import toml
from jinja2.ext import Extension
from jinja2.nodes import Const, EvalContext, ExprStmt, Impossible, Name, Output
from jinja2.utils import contextfunction

from shuup.xtheme.rendering import render_placeholder
from shuup.xtheme.view_config import Layout


class Unflattenable(Exception):
    """
    Exception raised when a node list can't be flattened into a constant.
    """


class NonConstant(ValueError):
    """
    Exception raised when something expected to be constant... is not.
    """


class NestingError(ValueError):
    """
    Exception raised when a template's placeholder/column/row/plugin
    hierarchy is out of whack.
    """


def flatten_const_node_list(environment, node_list):
    """
    Try to flatten the given node list into a single string.

    :param environment: Jinja2 environment
    :type environment: jinja2.environment.Environment
    :param node_list: List of nodes
    :type node_list: list[jinja2.nodes.Node]
    :return: String of content
    :rtype: str
    :raise Unflattenable: Raised when the node list can't be flattened into
                          a constant
    """
    output = []
    eval_ctx = EvalContext(environment)
    for node in node_list:
        if isinstance(node, Output):  # pragma: no branch
            for node in node.nodes:
                try:
                    const = node.as_const(eval_ctx=eval_ctx)
                    if not isinstance(const, six.text_type):
                        raise Unflattenable(const)
                    output.append(const)
                except Impossible:
                    raise Unflattenable(node)
        else:
            # Very unlikely, but you know.
            raise Unflattenable(node)  # pragma: no cover
    return "".join(output)


def parse_constantlike(environment, parser):
    """
    Parse the next expression as a "constantlike" expression.

    Expression trees that fold into constants are constantlike,
    as are bare variable names.

    :param environment: Jinja2 environment
    :type environment: jinja2.environment.Environment
    :param parser: Template parser
    :type parser: jinja2.parser.Parser
    :return: constant value of any type
    :rtype: object
    """
    expr = parser.parse_expression()
    if isinstance(expr, Name):  # bare names are accepted
        return expr.name
    try:
        return expr.as_const(EvalContext(environment))
    except Impossible:
        raise NonConstant("Not constant: %r" % expr)


class _PlaceholderManagingExtension(Extension):
    """
    Superclass (could be mixin) with helpers for getting the currently
    active layout object from a parser.
    """
    def _get_layout(self, parser, accept_none=False):
        """
        Get the currently managed Layout from the parser.

        :param parser: Template parser
        :type parser: jinja2.parser.Parser
        :param accept_none: Whether or not to accept the eventuality that
                            there's no current layout. If False (the
                            default), a `NestingError` is raised.
        :type accept_none: bool
        :return: The current layout
        :rtype: shuup.xtheme.view_config.Layout
        :raises NestingError: Raised if there's no current layout and
                              that's not okay.
        """
        cfg = getattr(parser, "_xtheme_placeholder_layout", None)
        if not accept_none and cfg is None:
            raise NestingError("No current `placeholder` block!")
        return cfg

    def _new_layout(self, parser, placeholder_name):
        """
        Begin a new layout for the given placeholder in the parser.

        :param parser: Template parser
        :type parser: jinja2.parser.Parser
        :param placeholder_name: The name of the placeholder.
        :type placeholder_name: str
        :return: The new layout
        :rtype: shuup.xtheme.view_config.Layout
        :raises NestingError: Raised if there's a layout going on already.
        """
        curr_layout = self._get_layout(parser, accept_none=True)
        if curr_layout is not None:
            raise NestingError(
                "Can't nest `placeholder`s! (Currently in %r, trying to start %r)" % (
                    curr_layout.placeholder_name,
                    placeholder_name
                )
            )
        layout = Layout(None, placeholder_name=placeholder_name)
        parser._xtheme_placeholder_layout = layout
        return self._get_layout(parser)

    def _end_layout(self, parser):
        """
        End the current layout in the parser and return the serialized contents.

        :param parser: Template parser
        :type parser: jinja2.parser.Parser
        :return: The serialized layout
        :rtype: dict
        """
        layout = self._get_layout(parser)
        parser._xtheme_placeholder_layout = None
        return layout.serialize()


def noop_node(lineno):
    """
    Return a no-op node (compiled into a single `0`).

    :param lineno: Line number for the node
    :type lineno: int
    :return: Node
    :rtype: jinja2.nodes.ExprStmt
    """
    return ExprStmt(Const(0)).set_lineno(lineno)


class PlaceholderExtension(_PlaceholderManagingExtension):
    """
    `PlaceholderExtension` manages `{% placeholder <NAME> [global] %}` ...
      `{% endplaceholder %}`.

    * The `name` can be any Jinja2 expression that can be folded into a
      constant, with the addition of bare variable names such as `name`
      meaning the same as `"name"`. This makes it slightly easier to write
      templates.
    * The body of this block is actually discarded; only the inner
      `column`, `row` and `plugin` directives have any meaning.  (A
      parser-time `Layout` object is created and populated during parsing
      of this block.)
    * An optional ``global`` parameter can be used to specify that the
      configuration for this placeholder should be "global" across
      different views (although currently that only applies to placeholders
      within the same template, i.e, if you defined the same global
      placeholder in different templates they will not share configuration,
      but an included or base template that is rendered by different views
      will).
    """
    tags = set(['placeholder'])

    def parse(self, parser):
        """
        Parse a placeholder!

        :param parser: Template parser
        :type parser: jinja2.parser.Parser
        :return: Output node for rendering a placeholder.
        :rtype: jinja2.nodes.Output
        """
        lineno = next(parser.stream).lineno
        global_type = bool(parser.stream.look().value == "global")
        if global_type:
            # Do some special-case parsing for global placeholders
            placeholder_name = six.text_type(parser.stream.current.value)
            next(parser.stream)
            next(parser.stream)
        else:
            placeholder_name = six.text_type(parse_constantlike(self.environment, parser))
        self._new_layout(parser, placeholder_name)
        parser.parse_statements(['name:endplaceholder'], drop_needle=True)
        # Body parsing will have, as a side effect, populated the current layout
        layout = self._end_layout(parser)
        args = [
            Const(placeholder_name),
            Const(layout),
            Const(parser.name),
            Const(global_type),
        ]
        return Output([self.call_method('_render_placeholder', args)]).set_lineno(lineno)

    @contextfunction
    def _render_placeholder(self, context, placeholder_name, layout, template_name, global_type):
        return render_placeholder(
            context,
            placeholder_name=placeholder_name,
            default_layout=layout,
            template_name=template_name,
            global_type=global_type,
        )


class LayoutPartExtension(_PlaceholderManagingExtension):
    """
    Parser for row and column tags.

    Syntax for the row and column tags is::

      {% row %}
          {% column [SIZES] %}...{% endcolumn %}
      {% endrow %}

    * Rows map to `LayoutRow` objects and columns map to `LayoutCell`.

    * For a single-cell layout, these are not necessary.
      ``{% plugin %}`` invocations without preceding
      ``{% row %}``/``{% column %}`` directives imply a single
      row and a single column.
    """

    tags = set(['column', 'row'])

    def parse(self, parser):
        """
        Parse a column or row.

        :param parser: Template parser
        :type parser: jinja2.parser.Parser
        :return: A null output node.
        :rtype: jinja2.nodes.Node
        """
        start = next(parser.stream)
        lineno = start.lineno
        arg = None
        if parser.stream.current.type != "block_end":
            arg = parser.parse_expression()  # Parse any expression
        cfg = self._get_layout(parser)

        if start.value == "row":
            self._begin_row(cfg, arg)
        elif start.value == "column":
            self._begin_column(cfg, arg)

        parser.parse_statements(["name:end%s" % start.value], drop_needle=True)
        # Body parsing is also a no-op here; the layout is populated already

        return noop_node(lineno)

    def _begin_row(self, cfg, arg):
        if arg is not None:
            raise ValueError("`row`s do not take arguments at present (got %r)" % arg)
        cfg.begin_row()

    def _begin_column(self, cfg, arg):
        sizes = {}
        if arg is not None:
            try:
                sizes = arg.as_const(eval_ctx=EvalContext(self.environment))
            except Impossible:
                raise ValueError("Invalid argument for `column`: %r" % arg)
            if not isinstance(sizes, dict):
                raise ValueError("Argument for `column` must be a dict: %r" % arg)
        cfg.begin_column(sizes)


class PluginExtension(_PlaceholderManagingExtension):
    """
    Parser for plugin tags.

    Syntax for plugin tag is::

      {% plugin <NAME> %}...{% endplugin %}

    * The (optional) body of the plugin block is expected to be a Jinja2
      AST that can be folded into a constant.  Generally this means a
      single block of text (``{% raw }``/``{% endraw %}`` is okay!).

    * The contents of the body, if set, must be valid `TOML markup
      <https://github.com/toml-lang/toml>`_.  The TOML is parsed during
      Jinja2 parse time into a dict, which in turn is folded into the
      layout description object.  This means only the initial parsing of
      the template incurs whatever performance hit there is in parsing
      TOML; the Jinja2 bccache should take care of the rest.
    """
    tags = set(['plugin'])

    def parse(self, parser):
        """
        Parse a column or row.

        :param parser: Template parser
        :type parser: jinja2.parser.Parser
        :return: A null output node.
        :rtype: jinja2.nodes.Node
        """
        lineno = next(parser.stream).lineno
        name = parse_constantlike(self.environment, parser)  # Parse the plugin name.
        body = parser.parse_statements(['name:endplugin'], drop_needle=True)
        layout = self._get_layout(parser)
        config = None
        if body:
            try:
                config = flatten_const_node_list(self.environment, body)
            except Unflattenable as uf:
                raise NonConstant("A `plugin` block may only contain static layout (found: %r)" % uf.args[0])
            config = toml.loads(config)
        layout.add_plugin(name, config)
        return noop_node(lineno)


EXTENSIONS = [
    LayoutPartExtension,
    PlaceholderExtension,
    PluginExtension,
]
