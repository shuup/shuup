# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import hashlib
import logging
import os
from datetime import datetime
from django.apps import apps
from django.contrib import messages
from django.db.models import Q
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, FormView, TemplateView, View

from shuup.admin.shop_provider import get_shop
from shuup.admin.supplier_provider import get_supplier
from shuup.admin.toolbar import NewActionButton
from shuup.admin.utils.permissions import has_permission
from shuup.admin.utils.picotable import ChoicesFilter, Column, DateRangeFilter, Picotable
from shuup.admin.utils.views import PicotableListView
from shuup.apps.provides import get_provide_objects
from shuup.core.models import BackgroundTaskExecution, BackgroundTaskExecutionStatus
from shuup.core.tasks import LOGGER, run_task
from shuup.importer.admin_module.forms import ImportForm, ImportSettingsForm
from shuup.importer.exceptions import ImporterError
from shuup.importer.utils import get_import_file_path, get_importer, get_importer_choices
from shuup.importer.utils.importer import FileImporter, ImportMode
from shuup.utils.django_compat import reverse

logger = logging.getLogger(__name__)


IMPORTER_NAMES_MAP = {importer.identifier: importer.name for importer in get_provide_objects("importers")}


class ImporterPicotable(Picotable):
    def get_verbose_name_plural(self):
        return _("Data imports")


class ImportProcessView(TemplateView):
    template_name = "shuup/importer/admin/import_process.jinja"

    def dispatch(self, request, *args, **kwargs):
        if not request.GET.get("importer"):
            return HttpResponseBadRequest(_("Invalid importer."))
        if not request.GET.get("n"):
            return HttpResponseBadRequest(_("File is missing."))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        mapping = dict()

        for field in request.POST.keys():
            if field.startswith("remap["):
                # remove the remap[] part
                field_name = field.replace("remap[", "")[:-1]
                mapping[field_name] = self.request.POST.getlist(field)

        supplier = get_supplier(request)
        shop = get_shop(request)
        run_task(
            "shuup.importer.tasks.import_file",
            stored=True,
            queue="data_import",
            importer=request.GET["importer"],
            import_mode=request.POST.get("import_mode") or ImportMode.CREATE_UPDATE.value,
            file_name=request.GET["n"],
            language=request.GET.get("lang"),
            shop_id=shop.pk,
            supplier_id=supplier.pk if supplier else None,
            user_id=request.user.pk,
            mapping=mapping,
        )
        messages.success(request, _("The import was queued!"))
        return redirect(reverse("shuup_admin:importer.import"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file_importer = FileImporter(
            importer=self.request.GET["importer"],
            import_mode=ImportMode.CREATE_UPDATE,
            file_name=self.request.GET["n"],
            language=self.request.GET.get("lang"),
            shop_id=get_shop(self.request),
            supplier_id=get_supplier(self.request),
        )
        file_importer.prepare()

        settings_form = ImportSettingsForm(data=self.request.POST if self.request.POST else None)
        if settings_form.is_bound:
            settings_form.is_valid()

        context["data"] = file_importer.data
        context["importer"] = file_importer.importer
        context["form"] = settings_form
        context["model_fields"] = file_importer.importer.get_fields_for_mapping()
        context["visible_rows"] = file_importer.data.rows[1:5]
        return context

    def get(self, request, *args, **kwargs):
        try:
            return self.render_to_response(self.get_context_data(**kwargs))
        except ImporterError:
            LOGGER.exception("Failed to process the file")
            messages.error(request, _("Failed to process the file."))
            return redirect(reverse("shuup_admin:importer.import"))


class ImportView(FormView):
    template_name = "shuup/importer/admin/import.jinja"
    form_class = ImportForm

    def post(self, request, *args, **kwargs):
        file = self.request.FILES["file"]
        basename, ext = os.path.splitext(file.name)

        import_name = "%s%s" % (hashlib.sha256(("%s" % datetime.now()).encode("utf-8")).hexdigest(), ext)
        full_path = get_import_file_path(import_name)
        if not os.path.isdir(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))

        with open(full_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        next_url = request.POST.get("next")
        importer = request.POST.get("importer")
        lang = request.POST.get("language")
        return redirect("%s?n=%s&importer=%s&lang=%s" % (next_url, import_name, importer, lang))

    def get_form_kwargs(self):
        kwargs = super(ImportView, self).get_form_kwargs()
        initial = kwargs.get("initial", {})
        initial["importer"] = self.request.GET.get("importer", initial.get("initial"))
        kwargs.update({"request": self.request, "initial": initial})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ImportView, self).get_context_data(**kwargs)

        # check whether the importer has a example file template
        # if so, we also add a url to download the example file
        importer = self.request.GET.get("importer")

        # no importer passed, get the first choice available
        if not importer:
            importers = list(get_importer_choices(self.request.user))
            if importers:
                importer = importers[0][0]

        if importer:
            importer_cls = get_importer(importer)
            context.update(importer_cls.get_help_context_data(self.request))
            context["importer"] = importer_cls

        return context


class ExampleFileDownloadView(View):
    def get(self, request, *args, **kwargs):
        importer = request.GET.get("importer")
        file_name = request.GET.get("file_name")
        if not importer or not file_name:
            return HttpResponseBadRequest(_("Invalid parameters."))

        importer_cls = get_importer(importer)
        if not importer_cls or not importer_cls.has_example_file():
            raise Http404(_("Invalid importer."))

        example_file = importer_cls.get_example_file(file_name)
        if not example_file:
            raise Http404(_("Invalid file name."))

        response = HttpResponse(content_type=example_file.content_type)
        response["Content-Disposition"] = "attachment; filename=%s" % example_file.file_name

        data = importer_cls.get_example_file_content(example_file, request)

        if not data:
            raise Http404(_("File was not found."))

        data.seek(0)
        response.write(data.getvalue())
        return response


def get_imports_queryset(request):
    # get only executions from tasks inside `data_import` queue
    queryset = BackgroundTaskExecution.objects.select_related("task", "task__user").filter(task__queue="data_import")

    if not has_permission(request.user, "importer.show-all-imports"):
        shop = get_shop(request)
        supplier = get_supplier(request)
        queryset = queryset.filter(
            Q(Q(task__shop=shop) | Q(task__shop__isnull=True)),
            Q(task__supplier=supplier),
        )

    return queryset


class ImportListView(PicotableListView):
    picotable_class = ImporterPicotable
    model = BackgroundTaskExecution
    default_columns = [
        Column("started_on", _("Import date"), sortable=True, filter_config=DateRangeFilter()),
        Column("importer", _("Importer"), sortable=False, display="get_importer"),
        Column("import_mode", _("Import mode"), sortable=False, display="get_import_mode"),
        Column("user", _("User"), sort_field="task__user", display="get_user"),
        Column(
            "status",
            _("Status"),
            sort_field="status",
            filter_config=ChoicesFilter(BackgroundTaskExecutionStatus.choices()),
        ),
    ]
    toolbar_buttons_provider_key = "import_list_toolbar_provider"
    mass_actions_provider_key = "import_list_mass_actions_provider"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns = self.default_columns

    def get_importer(self, instance):
        importer = instance.task.arguments["importer"]
        return IMPORTER_NAMES_MAP.get(importer, importer)

    def get_user(self, instance):
        return str(instance.task.user or "-")

    def get_import_mode(self, instance):
        return ImportMode(instance.task.arguments["import_mode"]).label

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Data imports")
        return context

    def get_toolbar(self):
        toolbar = super().get_toolbar()
        toolbar.append(
            NewActionButton(url=reverse("shuup_admin:importer.import.new"), text=_("Import file"), icon="fa fa-upload")
        )
        return toolbar

    def get_queryset(self):
        return get_imports_queryset(self.request).defer("result", "error_log")

    def get_object_url(self, instance):
        return reverse("shuup_admin:importer.import.detail", kwargs=dict(pk=instance.pk))

    def get_object_abstract(self, instance, item):
        return [
            {"text": item.get("importer"), "class": "header"},
            {"title": _("Importdate"), "text": item.get("started_on")},
            {"title": _("Mode"), "text": item.get("import_mode")},
            {"title": _("User"), "text": item.get("user")},
            {"title": _("Status"), "text": item.get("status")},
        ]


class ImportDetailView(DetailView):
    model = BackgroundTaskExecution
    template_name = "shuup/importer/admin/import_process_complete.jinja"

    def get_queryset(self):
        return get_imports_queryset(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = self.object.result

        context["new_objects"] = []
        context["updated_objects"] = []
        context["log_messages"] = []
        context["other_log_messages"] = []

        if result:
            context["log_messages"] = result.get("log_messages")
            context["other_log_messages"] = result.get("other_log_messages")

            new_objects = result.get("new_objects")
            updated_objects = result.get("updated_objects")

            if new_objects:
                model = apps.get_model(new_objects[0]["model"])
                pks = [obj["pk"] for obj in new_objects]
                context["new_objects"] = model.objects.filter(pk__in=pks).order_by("pk")

            if updated_objects:
                model = apps.get_model(updated_objects[0]["model"])
                pks = [obj["pk"] for obj in updated_objects]
                context["updated_objects"] = model.objects.filter(pk__in=pks).order_by("pk")

        return context
