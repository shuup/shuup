# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import json

from django.http.response import HttpResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from shoop.utils.excs import Problem
from shoop.xtheme._theme import get_theme_by_identifier
from shoop.xtheme.editing import could_edit
from shoop.xtheme.view_config import ViewConfig
from shoop.xtheme.views.forms import LayoutCellFormGroup

# since layouts will most likely break with multiple cells per row, we are
# limiting the amount.
ROW_CELL_LIMIT = 4


class EditorView(TemplateView):
    template_name = "shoop/xtheme/editor.jinja"
    xtheme_injection = False  # We don't need the editing injection here, so opt-out
    changed = False  # Overridden in `save_layout`

    def _get_default_layout(self):
        try:
            return json.loads(self.request.GET["default_config"])
        except (ValueError, KeyError):
            return None

    def get_context_data(self, **kwargs):  # doccov: ignore
        ctx = super(EditorView, self).get_context_data(**kwargs)
        ctx["layout"] = self.layout
        ctx["csrf_token_str"] = get_token(self.request)
        # ctx["layout_debug"] = pformat(ctx["layout"].serialize())
        ctx["current_cell_coords"] = self.current_cell_coords
        ctx["current_cell"] = self.current_cell
        ctx["form"] = self.form
        ctx["changed"] = self.changed
        ctx["cell_limit"] = ROW_CELL_LIMIT
        return ctx

    def dispatch(self, request, *args, **kwargs):  # doccov: ignore
        if not could_edit(request):
            raise Problem("No access to editing")
        self._populate_vars()
        if self.default_layout:
            self.view_config.save_default_placeholder_layout(self.placeholder_name, self.default_layout)
            # We saved the default layout, so get rid of the humongous GET arg and try again
            get_args = dict(self.request.GET.items())
            get_args.pop("default_config", None)
            return HttpResponseRedirect("%s?%s" % (self.request.path, urlencode(get_args)))
        return super(EditorView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):  # doccov: ignore
        command = request.POST.get("command")
        if command:
            dispatcher = getattr(self, "dispatch_%s" % command, None)
            if not callable(dispatcher):
                raise Problem("Unknown command %s" % command)
            dispatch_kwargs = dict(request.POST.items())
            rv = dispatcher(**dispatch_kwargs)
            if rv:
                return rv
            self.request.method = "GET"  # At this point, we won't want to cause form validation
            self.build_form()  # and it's not a bad idea to rebuild the form
            return super(EditorView, self).get(request, *args, **kwargs)

        if request.POST.get("save") and self.form and self.form.is_valid():
            self.form.save()
            self.save_layout()

        return super(EditorView, self).get(request, *args, **kwargs)

    def _populate_vars(self):
        theme = get_theme_by_identifier(self.request.GET["theme"])
        if not theme:
            raise Problem("Unable to determine current theme.")
        self.view_config = ViewConfig(
            theme=theme,
            view_name=self.request.GET["view"],
            draft=True
        )
        self.placeholder_name = self.request.GET["ph"]
        self.default_layout = self._get_default_layout()
        self.layout = self.view_config.get_placeholder_layout(
            placeholder_name=self.placeholder_name,
            default_layout=self.default_layout
        )
        (x, y) = self.current_cell_coords = (
            int(self.request.GET.get("x", -1)),
            int(self.request.GET.get("y", -1)),
        )
        self.current_cell = self.layout.get_cell(x=x, y=y)
        self.build_form()

    def build_form(self):
        if not self.current_cell:
            self.form = None
            return
        kwargs = {
            "layout_cell": self.current_cell
        }
        if self.request.method == "POST":
            kwargs["data"] = self.request.POST
            kwargs["files"] = self.request.FILES
        self.form = LayoutCellFormGroup(**kwargs)

    def save_layout(self, layout=None):
        self.view_config.save_placeholder_layout(
            placeholder_name=self.placeholder_name,
            layout=(layout or self.layout)
        )
        self.changed = True

    def dispatch_add_cell(self, y, **kwargs):
        y = int(y)
        if len(self.layout.rows[y].cells) >= ROW_CELL_LIMIT:
            raise ValueError(_("Cannot add more than %d cells in one row.") % ROW_CELL_LIMIT)

        if not (0 <= y < len(self.layout.rows)):
            # No need to raise an exception, really.
            # It must have been a honest mistake.
            return
        self.layout.rows[y].add_cell()
        self.save_layout()

    def dispatch_add_row(self, y=None, **kwargs):
        row = self.layout.insert_row(y)
        row.add_cell()  # For convenience, add a cell to the row.
        self.save_layout()

    def dispatch_del_row(self, y, **kwargs):
        self.layout.delete_row(y)
        self.save_layout()

    def dispatch_del_cell(self, x, y, **kwargs):
        self.layout.delete_cell(x, y)
        self.save_layout()

    def dispatch_change_plugin(self, plugin="", **kwargs):
        if self.current_cell:
            if not plugin:
                plugin = None
            self.current_cell.plugin_identifier = plugin
            self.save_layout()

    def dispatch_publish(self, **kwargs):
        self.view_config.publish()
        return HttpResponse("<html><script>parent.location.reload()</script>Published.</html>")

    def dispatch_revert(self, **kwargs):
        self.view_config.revert()
        return HttpResponse("<html><script>parent.location.reload()</script>Reverted.</html>")
