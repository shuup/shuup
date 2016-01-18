# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from markupsafe import Markup

from shoop.core.fields.tagged_json import TaggedJSONEncoder
from shoop.xtheme._theme import get_current_theme
from shoop.xtheme.editing import is_edit_mode
from shoop.xtheme.utils import get_html_attrs
from shoop.xtheme.view_config import ViewConfig


def get_view_config(context):
    """
    Get a view configuration object for a Jinja2 rendering context.

    :param context: Rendering context
    :type context: jinja2.runtime.Context
    :return: View config
    :rtype: shoop.xtheme.view_config.ViewConfig
    """
    # This uses the Jinja context's technically-immutable vars dict
    # to cache the view configuration. This is fine in our case, I'd say.
    request = context.get("request")
    config = context.vars.get("_xtheme_view_config")
    if config is None:
        view_object = context.get("view")
        if view_object:
            view_class = view_object.__class__
            view_name = view_class.__name__
        else:
            view_name = "UnknownView"
        config = ViewConfig(
            theme=get_current_theme(request),
            view_name=view_name,
            draft=is_edit_mode(request)
        )
        context.vars["_xtheme_view_config"] = config
    return config


def render_placeholder(context, placeholder_name, default_layout=None, template_name=None):  # doccov: noargs
    """
    Render a placeholder in a given context.

    See `PlaceholderRenderer` for argument docs.

    :return: Markup
    :rtype: Markup
    """
    renderer = PlaceholderRenderer(
        context,
        placeholder_name,
        default_layout=default_layout,
        template_name=template_name
    )
    return renderer.render()


class PlaceholderRenderer(object):
    """
    Main class for materializing a placeholder's contents during template render time.
    """
    # TODO: Maybe make this pluggable per-theme?

    def __init__(self, context, placeholder_name, default_layout=None, template_name=None):
        """
        :param context: Rendering context
        :type context: jinja2.runtime.Context
        :param placeholder_name: Placeholder name
        :type placeholder_name: str
        :param default_layout: Layout or serialized layout (from template configuration)
        :type default_layout: Layout|dict|None
        :param template_name: The actual template this node was in. Used to figure out whether the placeholder
                              lives in an `extends` parent, or in a child.
        :type template_name: str|None
        """
        self.context = context
        self.view_config = get_view_config(context)
        self.placeholder_name = placeholder_name
        self.template_name = template_name
        self.default_layout = default_layout
        self.layout = self.view_config.get_placeholder_layout(placeholder_name, self.default_layout)
        # Editing is only available for placeholders in the "base" template, i.e.
        # one that is not an `extend` parent.  Declaring placeholders in `include`d templates is fine,
        # but their configuration will not be shared among different uses of the same include.
        is_base = (self.template_name == self.context.name)
        self.edit = (is_base and is_edit_mode(context["request"]))

    def render(self):
        """
        Get this placeholder's rendered contents.

        :return: Rendered markup.
        :rtype: markupsafe.Markup
        """
        wrapper_start = "<div%s>" % get_html_attrs(self._get_wrapper_attrs())
        buffer = []
        write = buffer.append
        self._render_layout(write)
        content = "".join(buffer)
        return Markup("%(wrapper_start)s%(content)s%(wrapper_end)s" % {
            "wrapper_start": wrapper_start,
            "content": content,
            "wrapper_end": "</div>",
        })

    def _get_wrapper_attrs(self):
        attrs = {
            "class": ["xt-ph", "xt-ph-edit" if self.edit else None],
            "id": "xt-ph-%s" % self.placeholder_name
        }
        if self.edit:
            attrs["data-xt-placeholder-name"] = self.placeholder_name
            attrs["title"] = _("Click to edit placeholder: %s") % self.placeholder_name.title()
        return attrs

    def _render_layout(self, write):
        if self.edit and self.default_layout:
            self._render_default_layout_script_tag(write)
        for y, row in enumerate(self.layout):
            self._render_row(write, y, row)

    def _render_row(self, write, y, row):
        """
        Render a layout row into HTML.

        :param write: Writer function
        :type write: callable
        :param y: Row Y coordinate
        :type y: int
        :param row: Row object
        :type row: shoop.xtheme.view_config.LayoutRow
        """
        row_attrs = {
            "class": [self.layout.row_class, "xt-ph-row"]
        }
        if self.edit:
            row_attrs["data-xt-row"] = str(y)
        write("<div%s>" % get_html_attrs(row_attrs))
        for x, cell in enumerate(row):
            self._render_cell(write, x, cell)
        write("</div>\n")

    def _render_cell(self, write, x, cell):
        """
        Render a layout cell into HTML.

        :param write: Writer function
        :type write: callable
        :param x: Cell X coordinate
        :type x: int
        :param cell: Cell
        :type cell: shoop.xtheme.view_config.LayoutCell
        """
        classes = ["xt-ph-cell"]
        for breakpoint, width in cell.sizes.items():
            if width is None:
                continue
            if width <= 0:
                classes.append(self.layout.hide_cell_class_template % {"breakpoint": breakpoint, "width": width})
            else:
                classes.append(self.layout.cell_class_template % {"breakpoint": breakpoint, "width": width})
        cell_attrs = {
            "class": classes
        }
        if self.edit:
            cell_attrs.update({"data-xt-cell": str(x)})
        write("<div%s>" % get_html_attrs(cell_attrs))
        content = cell.render(self.context)
        if content is not None:  # pragma: no branch
            write(force_text(content))
        write("</div>")

    def _render_default_layout_script_tag(self, write):
        # This script tag is read by editor.js
        write("<script%s>" % get_html_attrs({
            "class": "xt-ph-default-layout",
            "type": "text/plain"
        }))
        layout = self.default_layout
        if hasattr(layout, "serialize"):
            layout = layout.serialize()
        # TODO: Might have to do something about ..
        # TODO: .. http://www.w3.org/TR/html5/scripting-1.html#restrictions-for-contents-of-script-elements
        write(TaggedJSONEncoder(separators=",:").encode(layout))
        write("</script>")
