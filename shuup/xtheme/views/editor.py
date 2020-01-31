# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

from django.http.response import HttpResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from shuup.utils.excs import Problem
from shuup.xtheme import XTHEME_GLOBAL_VIEW_NAME
from shuup.xtheme._theme import get_theme_by_identifier
from shuup.xtheme.editing import could_edit
from shuup.xtheme.layout import Layout
from shuup.xtheme.layout.utils import get_provided_layouts
from shuup.xtheme.view_config import ViewConfig
from shuup.xtheme.views.forms import LayoutCellFormGroup

# since layouts will most likely break with multiple cells per row, we are
# limiting the amount.
ROW_CELL_LIMIT = 4


class EditorView(TemplateView):
    template_name = "shuup/xtheme/editor.jinja"
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
            raise Problem(_("No access to editing."))
        self._populate_vars()
        if self.default_layout:
            self.view_config.save_default_placeholder_layout(self.placeholder_name, self.default_layout)
            # We saved the default layout, so get rid of the humongous GET arg and try again
            get_args = dict(self.request.GET.items())
            get_args.pop("default_config", None)
            global_type = get_args.pop("global_type", None)
            if global_type:
                get_args["view"] = XTHEME_GLOBAL_VIEW_NAME
            # We are overriding the view with XTHEME_GLOBAL_VIEW_NAME if this is a global placeholder
            return HttpResponseRedirect("%s?%s" % (self.request.path, urlencode(get_args)))
        return super(EditorView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):  # doccov: ignore
        command = request.POST.get("command")
        if command:
            dispatcher = getattr(self, "dispatch_%s" % command, None)
            if not callable(dispatcher):
                raise Problem(_("Unknown command: `%s`.") % command)
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

            # after we save the new layout configs, make sure to reload the saved data in forms
            # so the returned get() response contains updated data
            self.build_form()

            if request.POST.get("publish") == "1":
                return self.dispatch_publish()

        return self.get(request, *args, **kwargs)

    def _populate_vars(self):
        theme = get_theme_by_identifier(self.request.GET["theme"], self.request.shop)
        if not theme:
            raise Problem(_("Unable to determine the current theme."))
        view_name = self.request.GET["view"]
        global_type = self.request.GET.get("global_type", None)
        self.view_config = ViewConfig(
            theme=theme,
            shop=self.request.shop,
            view_name=view_name,
            draft=True,
            global_type=global_type,
        )

        # Let's store the layout data key for save here
        self.layout_data_key = self.request.GET.get("layout_data_key", None)

        # Let's use the layout identifier passed by the view to
        # fetch correct layout
        layout_identifier = self.request.GET.get("layout_identifier", None)
        layout_cls = Layout
        for provided_layout in get_provided_layouts():
            if provided_layout.identifier == layout_identifier:
                layout_cls = provided_layout

        self.placeholder_name = self.request.GET["ph"]
        self.default_layout = self._get_default_layout()
        self.layout = self.view_config.get_placeholder_layout(
            layout_cls=layout_cls,
            placeholder_name=self.placeholder_name,
            default_layout=self.default_layout,
            layout_data_key=self.layout_data_key
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
            "layout_cell": self.current_cell,
            "theme": self.view_config.theme,
            "request": self.request
        }
        if self.request.method == "POST":
            kwargs["data"] = self.request.POST
            kwargs["files"] = self.request.FILES
        self.form = LayoutCellFormGroup(**kwargs)

    def save_layout(self, layout=None):
        self.view_config.save_placeholder_layout(
            layout_data_key=self.layout_data_key,
            layout=(layout or self.layout)
        )
        self.changed = True

    def dispatch_add_cell(self, y, **kwargs):
        y = int(y)
        if len(self.layout.rows[y].cells) >= ROW_CELL_LIMIT:
            raise ValueError(_("Can't add more than %d cells in one row.") % ROW_CELL_LIMIT)

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

    def dispatch_move_row_to_index(self, from_y, to_y, **kwargs):
        self.layout.move_row_to_index(from_y, to_y)
        self.save_layout()

    def dispatch_move_cell_to_position(self, from_x, from_y, to_x, to_y, **kwargs):
        self.layout.move_cell_to_position(from_x, from_y, to_x, to_y)
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
        return HttpResponse("<html><script>parent.location.reload()</script>%s.</html>" % _("Published"))

    def dispatch_revert(self, **kwargs):
        self.view_config.revert()
        return HttpResponse("<html><script>parent.location.reload()</script>%s.</html>" % _("Reverted"))
