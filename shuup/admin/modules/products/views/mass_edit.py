# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from enumfields import EnumIntegerField

from shuup.admin.utils.views import MassEditMixin
from shuup.core.models import Category, Product, ShopProductVisibility


class MassEditForm(forms.Form):
    name = forms.CharField(max_length=255, required=False)
    default_price_value = forms.DecimalField(label="Default Price", required=False)
    visibility = EnumIntegerField(ShopProductVisibility).formfield(label=_("Visibility"), required=False)
    primary_category = forms.ModelChoiceField(
        label=_("Primary Category"), queryset=Category.objects.all(), required=False)
    purchasable = forms.BooleanField(label=_("Purchasable"), required=False)


class ProductMassEditView(MassEditMixin, FormView):
    title = _("Mass Edit: Products")
    form_class = MassEditForm

    def form_valid(self, form):
        for product in Product.objects.filter(id__in=self.ids):
            shop_product = product.get_shop_instance(self.request.shop)

            for k, v in six.iteritems(form.cleaned_data):
                if not v:
                    continue
                if hasattr(product, k):
                    setattr(product, k, v)
                if hasattr(shop_product, k):
                    setattr(shop_product, k, v)
            product.save()
            shop_product.save()

        messages.success(self.request, _("Products changed successfully"))
        self.request.session["mass_action_ids"] = []
        return HttpResponseRedirect(reverse("shuup_admin:product.list"))
