# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from shuup.xtheme.plugins._base import Plugin


class LayoutCell(object):
    """
    A single cell in a layout. Maps to Bootstrap's `col-XX-XX` classes.
    """

    def __init__(self, theme, plugin_identifier, config=None, sizes=None, align="", extra_classes=""):
        """
        Initialize a layout cell with a given plugin, config and sizing configuration.

        :param plugin_identifier: Plugin identifier string.
        :type plugin_identifier: str
        :param config: Config dict.
        :type config: dict|None
        :param sizes: Size dict.
        :type sizes: dict|None
        :param align: Align string.
        :type align: str
        """
        self.theme = theme
        self.sizes = dict(sizes or {})
        self.plugin_identifier = plugin_identifier
        self.config = config or {}
        self.align = align
        self.extra_classes = extra_classes

    @property
    def plugin_class(self):
        """
        Get the actual plugin class for this cell, or None if the plugin class isn't available.

        :return: Plugin or None.
        :rtype: Plugin|None
        """
        return Plugin.load(self.plugin_identifier, self.theme)

    @property
    def plugin_name(self):
        """
        Get the name of the plugin in this cell for display purposes.

        :return: Plugin name string.
        :rtype: str
        """
        plugin_class = self.plugin_class
        return getattr(plugin_class, "name", "None")

    def instantiate_plugin(self):
        """
        Instantiate the plugin with the current config.

        :return: Instantiated plugin (if a class is available).
        :rtype: Plugin|None
        """
        plugin_class = self.plugin_class
        if callable(plugin_class):
            return plugin_class(config=self.config)
        return None

    def render(self, context):
        """
        Return the plugin's rendered content.

        :param context: Jinja2 rendering context.
        :type context: jinja2.runtime.Context
        :return: string of content.
        :rtype: str
        """
        if not self.plugin_identifier:
            return ""  # Null!
        plugin_inst = self.instantiate_plugin()
        if plugin_inst is None:
            return mark_safe("<!-- %s? -->" % self.plugin_identifier)
        if plugin_inst.is_context_valid(context=context):
            return plugin_inst.render(context=context)
        else:
            return ""

    @classmethod
    def unserialize(cls, theme, data):
        """
        Unserialize a dict of layout cell data into a new cell.

        :param data: Layout cell data dict.
        :type data: dict
        :return: New cell.
        :rtype: LayoutCell
        """
        return cls(
            theme,
            plugin_identifier=data.get("plugin"),
            config=data.get("config"),
            sizes=data.get("sizes"),
            align=data.get("align", ""),
            extra_classes=data.get("extra_classes", "")
        )

    def serialize(self):
        """
        Serialize this cell into a dict.

        :return: Layout cell data dict.
        :rtype: dict
        """
        return dict((k, v) for (k, v) in (
            ("plugin", self.plugin_identifier),
            ("config", self.config),
            ("sizes", self.sizes),
            ("align", self.align),
            ("extra_classes", self.extra_classes),
        ) if k and v)


class LayoutRow(object):
    """
    A single row in a layout. Maps to Bootstrap's `row` class.
    """
    # TODO: Add responsive hiding to full rows?

    def __init__(self, theme, cells=None):
        """
        :param cells: Optional iterable of LayoutCells to populate this LayoutRow with.
        :type rows: Iterable[LayoutCell]|None
        """
        self.theme = theme
        self.cells = []
        if cells:
            self.cells.extend(cells)

    def __iter__(self):
        """
        Iterate over the cells in this row.

        :return: Iterable of cells
        :rtype: Iterable[LayoutCell]
        """
        return iter(self.cells)

    def __len__(self):
        """
        Return the number of cells in this row.

        :rtype: int
        """
        return len(self.cells)

    @classmethod
    def unserialize(cls, theme, data):
        """
        Unserialize a dict of layout row data into a new row, along with all cell children.

        :param data: Layout row data dict.
        :type data: dict
        :return: New row.
        :rtype: LayoutRow
        """
        cells = [LayoutCell.unserialize(theme, cell_data) for cell_data in data["cells"]]
        return cls(theme, cells=cells)

    def serialize(self):
        """
        Serialize this row into a dict.

        :return: Layout row data dict.
        :rtype: dict
        """
        return {
            "cells": [c.serialize() for c in self]
        }

    def add_cell(self, sizes=None):
        """
        Add an empty cell to this row. Used by the editor API.

        :param sizes: An optional size dict, see `LayoutCell`.
        :type sizes: dict|None
        :return: The new layout cell.
        :rtype: LayoutCell
        """
        cell = LayoutCell(self.theme, plugin_identifier=None, sizes=sizes)
        self.cells.append(cell)
        return cell


class Layout(object):
    """
    The layout (row, cell and plugin configuration) for a single placeholder.
    """
    identifier = "xtheme-default-layout"
    row_class = "row"
    cell_class_template = "col-%(breakpoint)s-%(width)s"
    hide_cell_class_template = "hidden-%(breakpoint)s"

    def __init__(self, theme, placeholder_name, rows=None):
        """
        :param placeholder_name: The name of the placeholder. Could be None.
        :type placeholder_name: str|None
        :param rows: Optional iterable of LayoutRows to populate this Layout with.
        :type rows: Iterable[LayoutRow]|None
        """
        self.theme = theme
        self.placeholder_name = placeholder_name
        self.rows = []
        if rows:
            self.rows.extend(rows)

    def get_help_text(self, context):
        """
        Help text for this placeholder box shown at the top of the
        editable layout.

        :param context: Jinja2 rendering context.
        :type context: jinja2.runtime.Context
        :return: Help text for this layout.
        :rtype: str
        """
        return _("Content in this box is shown to all user types without limitations.")

    def is_valid_context(self, context):
        """
        :param context: Jinja2 rendering context.
        :type context: jinja2.runtime.Context
        :return: Whether the current context is valid for this layout.
        :rtype: bool
        """
        return True

    def get_layout_data_suffix(self, context):
        """
        Layout data suffix which is used to save layout data to view config.

        With layout data suffix you can define data keys that is only available
        for certain contexts. Make sure that you validate the context for
        variables that is used to form this suffix.

        :param context: Jinja2 rendering context.
        :type context: jinja2.runtime.Context
        :rtype: str
        """
        return ""

    @classmethod
    def unserialize(cls, theme, data, placeholder_name=None):
        """
        Unserialize a dict of layout data into a new layout, with all rows and cells.

        :param data: Layout data dict.
        :type data: dict
        :param placeholder_name: Placeholder name if none is specified in the data.
        :type placeholder_name: str
        :return: New layout.
        :rtype: Layout
        """
        rows = [LayoutRow.unserialize(theme, row_data) for row_data in data["rows"]]
        return cls(
            theme,
            placeholder_name=data.get("name") or placeholder_name,
            rows=rows
        )

    def serialize(self):
        """
        Serialize this layout into a dict.

        :return: Layout data dict.
        :rtype: dict
        """
        return {
            "rows": [r.serialize() for r in self.rows],
            "name": self.placeholder_name
        }

    def __iter__(self):
        """
        Iterate over the rows in this layout.

        :return: Iterable of rows.
        :rtype: Iterable[LayoutRow]
        """
        return iter(self.rows)

    def __len__(self):
        """
        Return the number of rows in this layout.

        :rtype: int
        """
        return len(self.rows)

    def begin_row(self):
        """
        Begin a new row in the layout.

        This is internally used by `LayoutPartExtension`, but could just as well be
        used to programmatically create layouts for whichever purpose.

        :return: The newly created row.
        :rtype: LayoutRow
        """
        return self.insert_row()

    def begin_column(self, sizes=None):
        """
        Begin a new column (cell) in the layout, in the last row.

        If no rows exist, one is implicitly created, for your convenience.
        The newly created cell has no plugin or configuration.

        This is internally used by `LayoutPartExtension`, but could just as well be
        used to programmatically create layouts for whichever purpose.

        :param sizes: The size dictionary to pass to `LayoutCell`.
        :return: The newly created cell
        :rtype: LayoutCell
        """
        if not self.rows:
            self.begin_row()
        return self.rows[-1].add_cell(sizes=sizes)

    def add_plugin(self, plugin_identifier, config):
        """
        Configure a plugin in the last row and cell of the layout.

        If no rows or cells exist, one row and one cell is implicitly created.

        This is internally used by `LayoutPartExtension`, but could just as well be
        used to programmatically create layouts for whichever purpose.

        :param plugin_identifier: Plugin identifier string.
        :type plugin_identifier: str
        :param config: Configuration dict.
        :type config: dict
        :return: The configured cell.
        :rtype: LayoutCell
        """
        if not self.rows:
            self.begin_row()
        if not self.rows[-1].cells:
            self.begin_column()
        cell = self.rows[-1].cells[-1]
        cell.plugin_identifier = force_text(plugin_identifier)
        cell.config = config
        return cell

    def get_cell(self, x, y):
        """
        Get a layout cell indicated by the given (zero-based) coordinates.

        If the coordinates are out of range, returns None.

        :param x: X (horizontal) coordinate.
        :type x: int
        :param y: Y (vertical) coordinate.
        :type y: int
        :return: Layout cell.
        :rtype: LayoutCell|None
        """
        x = int(x)
        y = int(y)
        if 0 <= y < len(self.rows):
            row = self.rows[y]
            if 0 <= x < len(row):
                return row.cells[x]
        return None

    def insert_row(self, y=None):
        """
        Insert a new row at the given zero-based row and return it.

        If `y` is None, the row in inserted at the end.

        :param y: Y coordinate.
        :type y: int
        :return: The new layout row.
        :rtype: LayoutRow
        """
        if y is None:
            y = len(self.rows)
        y = int(y)
        if not (0 <= y <= len(self.rows)):
            return
        row = LayoutRow(self.theme)
        self.rows.insert(y, row)
        return row

    def delete_row(self, y):
        """
        Delete the y'th (zero-based) row.

        If `y` is out of bounds, nothing is done.

        :param y: Y coordinate.
        :type y: int
        :return: Was something done?
        :rtype: bool
        """
        y = int(y)
        if not (0 <= y < len(self.rows)):
            return False

        self.rows.pop(y)

        return True

    def move_row_to_index(self, from_y, to_y):
        """
        Move the y'th row to the specified zero-based index.

        If `y` or index are out of bounds, nothing is done.

        :param from_y: current Y coordinate.
        :type from_y: int
        :param to_y: new Y coordinate.
        :type to_y: int
        :return: Was something done?
        :rtype: bool
        """
        from_y = int(from_y)
        to_y = int(to_y)
        if not (0 <= from_y < len(self.rows)) or not (0 <= to_y < len(self.rows)):
            return False
        self.rows.insert(to_y, self.rows.pop(from_y))
        return True

    def move_cell_to_position(self, from_x, from_y, to_x, to_y):
        """
        Move the layout cell to the specified zero-based coordinates.

        If the coordinates are out of range, nothing is done.

        :param from_x: X (horizontal) coordinate of the cell to move.
        :type from_x: int
        :param from_y: Y (vertical) coordinate of the cell to move.
        :type from_y: int
        :param to_x: X (horizontal) coordinate of the cell after moving.
        :type to_x: int
        :param to_y: Y (vertical) coordinate of the cell after moving.
        :type to_y: int
        :return: Was something done?
        :rtype: bool
        """
        from_x = int(from_x)
        from_y = int(from_y)
        to_x = int(to_x)
        to_y = int(to_y)

        if not (0 <= from_y < len(self.rows)) or not(0 <= from_x < len(self.rows[from_y])):
            return False
        if not (0 <= to_y < len(self.rows)) or not (0 <= to_x <= len(self.rows[to_y])):
            return False
        cell_to_move = self.rows[from_y].cells.pop(from_x)
        self.rows[to_y].cells.insert(to_x, cell_to_move)
        if not len(self.rows[from_y]):
            self.delete_row(from_y)
        return True

    def delete_cell(self, x, y):
        """
        Delete a layout cell indicated by the given (zero-based) coordinates.

        If the coordinates are out of range, nothing is done.

        :param x: X (horizontal) coordinate.
        :type x: int
        :param y: Y (vertical) coordinate.
        :type y: int
        :return: Was something done?
        :rtype: bool
        """
        x = int(x)
        y = int(y)
        if 0 <= y < len(self.rows):
            row = self.rows[y]
            if 0 <= x < len(row):
                row.cells.pop(x)
                return True
        return False
