# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView

from shuup.core.models import Supplier


class SupplierDeleteView(RedirectView):
    permanent = False
    pk = None

    def dispatch(self, request, *args, **kwargs):
        if self.pk is None:
            self.pk = kwargs.pop("pk")
        return super(SupplierDeleteView, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        if settings.SHUUP_ENABLE_MULTIPLE_SUPPLIERS:
            return reverse("shuup_admin:shuup_multivendor.vendor.list")
        else:
            return reverse("shuup_admin:supplier.list")

    def post(self, request, *args, **kwargs):
        try:
            supplier = Supplier.objects.get(pk=self.pk)
            supplier.soft_delete()
            messages.success(request, _(u"%s has been marked deleted.") % supplier)
        except Supplier.DoesNotExist:
            messages.error(request, _(u"Supplier not found."))
        return super(SupplierDeleteView, self).post(request, *args, **kwargs)
