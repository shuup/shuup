# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.http.response import HttpResponseRedirect
from django.utils.translation import get_language, ugettext as _
from django.views.generic import DetailView

from shuup.core.models import Product, ProductMode, ShopProduct, Supplier
from shuup.front.utils.product import get_product_context
from shuup.utils.django_compat import reverse
from shuup.utils.excs import Problem, extract_messages


class ProductDetailView(DetailView):
    template_name = "shuup/front/product/detail.jinja"
    model = Product
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.language(get_language()).select_related("primary_image")

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        language = self.language = get_language()

        supplier_pk = self.kwargs.get("supplier_pk")
        if supplier_pk:
            supplier = Supplier.objects.enabled(shop=self.request.shop).filter(id=supplier_pk).first()
        else:
            shop_product = self.object.get_shop_instance(self.request.shop, allow_cache=True)
            supplier = shop_product.get_supplier(self.request.customer)

        context.update(get_product_context(self.request, self.object, language, supplier))
        # TODO: Maybe add hook for ProductDetailView get_context_data?
        # dispatch_hook("get_context_data", view=self, context=context)
        return context

    def get(self, request, *args, **kwargs):
        product = self.object = self.get_object()

        if product.mode == ProductMode.VARIATION_CHILD:
            # redirect to parent url with child pre-selected
            parent_url = reverse(
                "shuup:product", kwargs=dict(pk=product.variation_parent.pk, slug=product.variation_parent.slug)
            )
            return HttpResponseRedirect("{}?variation={}".format(parent_url, product.sku))

        try:
            shop_product = self.shop_product = product.get_shop_instance(request.shop, allow_cache=True)
        except ShopProduct.DoesNotExist:
            raise Problem(_(u"Error! This product is not available in this shop."))

        errors = list(shop_product.get_visibility_errors(customer=request.customer))

        if errors:
            raise Problem("\n".join(extract_messages(errors)))

        return super(ProductDetailView, self).get(request, *args, **kwargs)
