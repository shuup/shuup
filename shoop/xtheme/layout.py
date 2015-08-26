# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from shoop.xtheme.plugins import Plugin


class LayoutCell(object):
    """
    A single cell in a layout. Maps to Bootstrap's `col-XX-XX` classes.
    """

    def __init__(self, plugin_identifier, config=None, sizes=None):
        """
        Initialize a layout cell with a given plugin, config and sizing configuration.

        :param plugin_identifier: Plugin identifier string
        :type plugin_identifier: str
        :param config: Config dict
        :type config: dict|None
        :param sizes: Size dict
        :type sizes: dict|None
        """
        self.sizes = dict(sizes or {})
        self.plugin_identifier = plugin_identifier
        self.config = config or {}

    @property
    def plugin_class(self):
        """
        Get the actual plugin class for this cell, or None if the plugin class isn't available.

        :return: Plugin or None.
        :rtype: Plugin|None
        """
        return Plugin.load(self.plugin_identifier)

    def render(self, context):
        plugin_class = self.plugin_class
        if plugin_class is None:
            return mark_safe("<!-- %s? -->" % self.plugin_identifier)
        assert callable(plugin_class)
        return plugin_class(config=self.config).render(context=context)

    @classmethod
    def unserialize(cls, data):
        """
        Unserialize a dict of layout cell data into a new cell.

        :param data: Layout cell data dict
        :type data: dict
        :return: New cell
        :rtype: LayoutCell
        """
        return cls(
            plugin_identifier=data["plugin"],
            config=data["config"],
            sizes=data.get("sizes")
        )

    def serialize(self):
        """
        Serialize this cell into a dict.

        :return: Layout cell data dict
        :rtype: dict
        """
        return {
            "plugin": self.plugin_identifier,
            "config": self.config,
            "sizes": self.sizes
        }


class LayoutRow(object):
    """
    A single row in a layout. Maps to Bootstrap's `row` class.
    """
    # TODO: Add responsive hiding to full rows?

    def __init__(self, cells=None):
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

    @classmethod
    def unserialize(cls, data):
        """
        Unserialize a dict of layout row data into a new row, along with all cell children.

        :param data: Layout row data dict
        :type data: dict
        :return: New row
        :rtype: LayoutRow
        """
        cells = [LayoutCell.unserialize(cell_data) for cell_data in data["cells"]]
        return cls(cells=cells)

    def serialize(self):
        """
        Serialize this row into a dict.

        :return: Layout row data dict
        :rtype: dict
        """
        return {
            "cells": [c.serialize() for c in self]
        }


class Layout(object):
    """
    The layout (row, cell and plugin configuration) for a single placeholder.
    """

    row_class = "row"
    cell_class_template = "col-%(breakpoint)s-%(width)s"
    hide_cell_class_template = "hidden-%(breakpoint)s"

    def __init__(self, placeholder_name, rows=None):
        """
        :param placeholder_name: The name of the placeholder. Could be None.
        :type placeholder_name: str|None
        :param rows: Optional iterable of LayoutRows to populate this Layout with.
        :type rows: Iterable[LayoutRow]|None
        """
        self.placeholder_name = placeholder_name
        self.rows = []
        if rows:
            self.rows.extend(rows)

    @classmethod
    def unserialize(cls, data):
        """
        Unserialize a dict of layout data into a new layout, with all rows and cells.

        :param data: Layout data dict
        :type data: dict
        :return: New layout
        :rtype: Layout
        """
        rows = [LayoutRow.unserialize(row_data) for row_data in data["rows"]]
        return cls(
            placeholder_name=data.get("name"),
            rows=rows
        )

    def serialize(self):
        """
        Serialize this layout into a dict.

        :return: Layout data dict
        :rtype: dict
        """
        return {
            "rows": [r.serialize() for r in self.rows],
            "name": self.placeholder_name
        }

    def __iter__(self):
        """
        Iterate over the rows in this layout.

        :return: Iterable of rows
        :rtype: Iterable[LayoutRow]
        """
        return iter(self.rows)

    def begin_row(self):
        """
        Begin a new row in the layout.

        This is internally used by `LayoutPartExtension`, but could just as well be
        used to programmatically create layouts for whichever purpose.

        :return: The newly created row
        :rtype: LayoutRow
        """
        row = LayoutRow()
        self.rows.append(row)
        return row

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
        cell = LayoutCell(None, sizes=sizes)
        self.rows[-1].cells.append(cell)
        return cell

    def add_plugin(self, plugin_identifier, config):
        """
        Configure a plugin in the last row and cell of the layout.

        If no rows or cells exist, one row and one cell is implicitly created.

        This is internally used by `LayoutPartExtension`, but could just as well be
        used to programmatically create layouts for whichever purpose.

        :param plugin_identifier: Plugin identifier string
        :type plugin_identifier: str
        :param config: Configuration dict
        :type config: dict
        :return: The configured cell
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
