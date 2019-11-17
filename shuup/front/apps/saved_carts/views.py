# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.transaction import atomic
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView, View
from django.views.generic.detail import SingleObjectMixin

from shuup.core.excs import ProductNotOrderableProblem
from shuup.core.models import OrderLineType, Product, ShopProduct
from shuup.core.utils.users import real_user_or_none
from shuup.front.models import StoredBasket
from shuup.front.views.dashboard import DashboardViewMixin
from shuup.utils.django_compat import force_text


class CartViewMixin(object):
    model = StoredBasket

    def get_queryset(self):
        qs = super(CartViewMixin, self).get_queryset()
        return qs.filter(persistent=True, deleted=False, customer=self.request.customer, shop=self.request.shop)


class CartListView(DashboardViewMixin, CartViewMixin, ListView):
    template_name = 'shuup/saved_carts/cart_list.jinja'
    context_object_name = 'carts'


class CartDetailView(DashboardViewMixin, CartViewMixin, DetailView):
    template_name = 'shuup/saved_carts/cart_detail.jinja'
    context_object_name = 'cart'

    def get_queryset(self):
        qs = super(CartDetailView, self).get_queryset()
        return qs.prefetch_related("products")

    def get_context_data(self, **kwargs):
        context = super(CartDetailView, self).get_context_data(**kwargs)
        lines = []
        product_dict = {}
        for product in self.object.products.all():
            product_dict[product.id] = product

        for line in self.object.data.get("lines", []):
            if line.get("type", None) != OrderLineType.PRODUCT:
                continue
            product = product_dict[line["product_id"]]
            quantity = line.get("quantity", 0)
            lines.append({
                "product": product,
                "quantity": quantity,
            })
        context["lines"] = lines
        return context


class CartSaveView(View):
    def post(self, request, *args, **kwargs):
        title = request.POST.get("title", "")
        basket = request.basket
        if not request.customer:
            return JsonResponse({"ok": False}, status=403)
        if not title:
            return JsonResponse({"ok": False, "error": force_text(_("Please enter a basket title."))}, status=400)
        if basket.is_empty:
            return JsonResponse({"ok": False, "error": force_text(_("Can't save an empty basket."))}, status=400)
        saved_basket = StoredBasket(
            shop=basket.shop,
            customer=basket.customer,
            orderer=basket.orderer,
            creator=real_user_or_none(basket.creator),
            currency=basket.currency,
            prices_include_tax=basket.prices_include_tax,
            persistent=True,
            title=title,
            data=basket.storage.load(basket=basket),
            product_count=basket.smart_product_count)
        saved_basket.save()
        saved_basket.products.set(set(basket.product_ids))
        return JsonResponse({"ok": True}, status=200)


class CartAddAllProductsView(CartViewMixin, SingleObjectMixin, View):
    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs.get("pk"))

    def _get_supplier(self, shop_product, supplier_id, customer, quantity, shipping_address):
        if supplier_id:
            supplier = shop_product.suppliers.enabled().filter(pk=supplier_id).first()
        else:
            supplier = shop_product.get_supplier(customer, quantity, shipping_address)
        return supplier

    @atomic
    def post(self, request, *args, **kwargs):
        cart = self.get_object()
        basket = request.basket
        product_ids_to_quantities = basket.get_product_ids_and_quantities()
        errors = []
        quantity_added = 0
        for line in cart.data.get('lines', []):
            if line.get("type", None) != OrderLineType.PRODUCT:
                continue
            product = Product.objects.get(id=line.get("product_id", None))
            try:
                shop_product = product.get_shop_instance(shop=request.shop)
            except ShopProduct.DoesNotExist:
                errors.append({"product": line.text, "message": _("Product is not available in this shop.")})
                continue
            supplier = self._get_supplier(
                shop_product, line.get("supplier_id"), basket.customer, line.get("quantity"), basket.shipping_address)
            if not supplier:
                errors.append({"product": line.text, "message": _("Invalid supplier.")})
                continue

            try:
                quantity = line.get("quantity", 0)
                quantity_added += quantity
                product_quantity = quantity + product_ids_to_quantities.get(line["product_id"], 0)
                shop_product.raise_if_not_orderable(
                    supplier=supplier,
                    quantity=product_quantity,
                    customer=request.customer)
                basket.add_product(
                    supplier=supplier,
                    shop=request.shop,
                    product=product,
                    quantity=quantity)
            except ProductNotOrderableProblem as e:
                errors.append({"product": line["text"], "message": force_text(e.message)})
        return JsonResponse({
            "errors": errors,
            "success": force_text(_("%d product(s) added to cart." % quantity_added))
        }, status=200)


class CartDeleteView(CartViewMixin, SingleObjectMixin, View):
    def post(self, request, *args, **kwargs):
        cart = self.get_object()
        cart.deleted = True
        cart.save()
        return JsonResponse({"status": "success"}, status=200)
