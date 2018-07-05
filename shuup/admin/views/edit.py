# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.apps import apps
from django.http.response import (
    Http404, HttpResponseBadRequest, HttpResponseRedirect
)
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.admin.utils.urls import get_model_url, NoModelUrl
from shuup.utils.excs import Problem


class EditObjectView(View):
    def get(self, request):     # noqa (C901)
        model_name = request.GET.get("model")
        object_id = request.GET.get("pk", request.GET.get("id"))

        if not model_name or not object_id:
            return HttpResponseBadRequest(_("Invalid object."))

        url = None

        try:
            model = apps.get_model(model_name)
        except LookupError:
            return HttpResponseBadRequest(_("Invalid model."))

        instance = model.objects.filter(pk=object_id).first()
        if instance:
            required_permission = "%s.change_%s" % (instance._meta.app_label, instance._meta.model_name)
            missing_permissions = get_missing_permissions(request.user, [required_permission])

            if missing_permissions:
                reason = _("You do not have the required permission(s): %s") % ", ".join(missing_permissions)
                raise Problem(_("Can't view this page. %(reason)s") % {"reason": reason}, _("Unauthorized"))

            # try edit first
            try:
                url = get_model_url(
                    instance,
                    kind="edit",
                    user=request.user,
                    shop=get_shop(request),
                    required_permissions=[required_permission]
                )
            except NoModelUrl:
                # try detail
                try:
                    url = get_model_url(
                        instance,
                        kind="detail",
                        user=request.user,
                        shop=get_shop(request),
                        required_permissions=[required_permission]
                    )
                except NoModelUrl:
                    pass

            if url:
                # forward the mode param
                if request.GET.get("mode"):
                    url = "{}?mode={}".format(url, request.GET["mode"])

                return HttpResponseRedirect(url)

        raise Http404(_("Object not found"))
