# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from markupsafe import Markup

from shuup.core.fields.tagged_json import TaggedJSONEncoder
from shuup.xtheme._theme import get_current_theme
from shuup.xtheme.editing import is_edit_mode, may_inject
from shuup.xtheme.layout.utils import get_layout_data_key
from shuup.xtheme.utils import get_html_attrs
from shuup.xtheme.view_config import ViewConfig


def get_view_config(context, global_type=False):
    """
    Get a view configuration object for a Jinja2 rendering context.

    :param context: Rendering context
    :type context: jinja2.runtime.Context
    :param global_type: Boolean indicating whether this is a global type
    :type global_type: bool|False
    :return: View config
    :rtype: shuup.xtheme.view_config.ViewConfig
    """
    # This uses the Jinja context's technically-immutable vars dict
    # to cache the view configuration. This is fine in our case, I'd say.
    request = context.get("request")
    config_key = "_xtheme_global_view_config" if global_type else "_xtheme_view_config"
    config = context.vars.get(config_key)
    if (config is None):
        view_object = context.get("view")
        if view_object:
            view_class = view_object.__class__
            view_name = view_class.__name__
        else:
            view_name = "UnknownView"
        config = ViewConfig(
            theme=get_current_theme(request.shop),
            shop=request.shop,
            view_name=view_name,
            draft=is_edit_mode(request),
            global_type=global_type,
        )
        context.vars[config_key] = config
    return config


def render_placeholder(context, placeholder_name, default_layout=None, template_name=None,
                       global_type=False):  # doccov: noargs
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
        template_name=template_name,
        global_type=global_type,
    )
    return renderer.render()


class PlaceholderRenderer(object):
    """
    Main class for materializing a placeholder's contents during template render time.
    """
    # TODO: Maybe make this pluggable per-theme?

    def __init__(self, context, placeholder_name, default_layout=None, template_name=None, global_type=False):
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
        :param global_type: Boolean indicating whether this is a global placeholder
        :type global_type: bool|False
        """
        self.context = context
        self.view_config = get_view_config(context, global_type=global_type)
        self.placeholder_name = placeholder_name
        self.template_name = ("_xtheme_global_template_name" if global_type else template_name)
        self.default_layout = default_layout
        # Fetch all layouts for this placeholder context combination
        self.layouts = self.view_config.get_placeholder_layouts(context, placeholder_name, self.default_layout)
        self.global_type = global_type
        # For non-global placeholders, editing is only available for placeholders in the "base" template, i.e.
        # one that is not an `extend` parent.  Declaring placeholders in `include`d templates is fine,
        # but their configuration will not be shared among different uses of the same include.
        if global_type:
            self.edit = is_edit_mode(context["request"])
        else:
            is_base = (self.template_name == self.context.name)
            self.edit = (is_base and is_edit_mode(context["request"]))

    def render(self):
        """
        Get this placeholder's rendered contents.

        :return: Rendered markup.
        :rtype: markupsafe.Markup
        """
        if not may_inject(self.context):
            return ""

        full_content = ""
        for layout in self.layouts:
            wrapper_start = "<div%s>" % get_html_attrs(self._get_wrapper_attrs(layout))
            buffer = []
            write = buffer.append
            self._render_layout(write, layout)
            content = "".join(buffer)
            full_content += (
                "%(wrapper_start)s%(content)s%(wrapper_end)s" % {
                    "wrapper_start": wrapper_start,
                    "content": content,
                    "wrapper_end": "</div>",
                })

        return Markup('<div class="placeholder-edit-wrap">%s</div>' % full_content)

    def _get_wrapper_attrs(self, layout):
        layout_data_key = get_layout_data_key(self.placeholder_name, layout, self.context)
        attrs = {
            "class": ["xt-ph", "xt-ph-edit" if self.edit else None, "xt-global-ph" if self.global_type else None],
            "id": "xt-ph-%s" % layout_data_key
        }
        if self.edit:
            # Pass layout editor to editor so we can fetch
            # correct layout for editing.
            attrs["data-xt-layout-identifier"] = layout.identifier

            # We need to pass layout data key here since this is the last
            # place whe have the context available before editor.
            attrs["data-xt-layout-data-key"] = layout_data_key
            attrs["data-xt-placeholder-name"] = self.placeholder_name
            attrs["data-xt-global-type"] = "global" if self.global_type else None
            attrs["title"] = _("Click to edit placeholder: %s") % self.placeholder_name.title()
        return attrs

    def _render_layout(self, write, layout):
        if self.edit:
            help_text = layout.get_help_text(self.context)
            if self.global_type:
                glopal_help_text = _(
                    "This placeholder is global and content of this placeholder is shown on all pages.")
                help_text += " " + force_text(glopal_help_text)
            ph_name = self.placeholder_name.replace("_", " ").title()
            tmpl = '<p class="placeholder-help-text">%s<span class="layout-identifier">%s</span></p>'
            write(tmpl % (help_text, ph_name))

        if self.edit and self.default_layout:
            self._render_default_layout_script_tag(write)

        for y, row in enumerate(layout):
            self._render_row(write, layout, y, row)

    def _render_row(self, write, layout, y, row):
        """
        Render a layout row into HTML.

        :param write: Writer function
        :type write: callable
        :param y: Row Y coordinate
        :type y: int
        :param row: Row object
        :type row: shuup.xtheme.view_config.LayoutRow
        """
        row_attrs = {
            "class": [layout.row_class, "xt-ph-row"]
        }
        if self.edit:
            row_attrs["data-xt-row"] = str(y)
        write("<div%s>" % get_html_attrs(row_attrs))
        for x, cell in enumerate(row):
            self._render_cell(write, layout, x, cell)
        write("</div>\n")

    def _render_cell(self, write, layout, x, cell):
        """
        Render a layout cell into HTML.

        :param write: Writer function
        :type write: callable
        :param x: Cell X coordinate
        :type x: int
        :param cell: Cell
        :type cell: shuup.xtheme.view_config.LayoutCell
        """
        classes = ["xt-ph-cell"]
        for breakpoint, width in cell.sizes.items():
            if width is None:
                continue
            if width <= 0:
                classes.append(layout.hide_cell_class_template % {"breakpoint": breakpoint, "width": width})
            else:
                classes.append(layout.cell_class_template % {"breakpoint": breakpoint, "width": width})

        classes.append(cell.align)
        if cell.extra_classes:
            classes.append(cell.extra_classes)

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
