# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from enumfields import EnumIntegerField

from shuup.admin.forms.widgets import (
    QuickAddCategoryMultiSelect, QuickAddCategorySelect
)
from shuup.admin.utils.views import MassEditMixin
from shuup.core.models import Category, Product, ShopProductVisibility


class MassEditForm(forms.Form):
    name = forms.CharField(max_length=255, required=False)
    default_price_value = forms.DecimalField(label="Default Price", required=False)
    visibility = EnumIntegerField(ShopProductVisibility).formfield(label=_("Visibility"), required=False)
    primary_category = forms.ModelChoiceField(
        label=_("Primary Category"), queryset=Category.objects.all_except_deleted(), required=False,
        widget=QuickAddCategorySelect())
    categories = forms.ModelMultipleChoiceField(
        label=_("Additional Categories"), queryset=Category.objects.all_except_deleted(), required=False,
        widget=QuickAddCategoryMultiSelect())
    purchasable = forms.BooleanField(label=_("Purchasable"), required=False)


class ProductMassEditView(MassEditMixin, FormView):
    title = _("Mass Edit: Products")
    form_class = MassEditForm

    def form_valid(self, form):
        query = Product.objects.filter(shop_products__shop=self.request.shop)

        if not isinstance(self.ids, six.string_types) and self.ids != "all":
            query = query.filter(shop_products__id__in=self.ids)

        for product in query:
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

        messages.success(self.request, _("Products changed."))
        self.request.session["mass_action_ids"] = []
        return HttpResponseRedirect(reverse("shuup_admin:shop_product.list"))
