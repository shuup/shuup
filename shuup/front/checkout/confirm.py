# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
from logging import getLogger

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shuup.core.models import OrderStatus
from shuup.front.basket import get_basket_order_creator
from shuup.front.checkout import CheckoutPhaseViewMixin
from shuup.utils.djangoenv import has_installed

logger = getLogger(__name__)


class ConfirmForm(forms.Form):
    product_ids = forms.CharField(widget=forms.HiddenInput(), required=True)
    accept_terms = forms.BooleanField(required=True, label=_(u"I accept the terms and conditions"))
    marketing = forms.BooleanField(required=False, label=_(u"I want to receive marketing material"), initial=False)
    comment = forms.CharField(widget=forms.Textarea(), required=False, label=_(u"Comment"))

    def __init__(self, *args, **kwargs):
        self.current_product_ids = kwargs.pop("current_product_ids", "")
        super(ConfirmForm, self).__init__(*args, **kwargs)

        field_properties = settings.SHUUP_CHECKOUT_CONFIRM_FORM_PROPERTIES
        for field, properties in field_properties.items():
            for prop in properties:
                setattr(self.fields[field], prop, properties[prop])

    def clean(self):
        product_ids = set(self.cleaned_data.get('product_ids', "").split(','))
        if product_ids != self.current_product_ids:
            raise forms.ValidationError(
                _("There has been a change in product availability. Please review your cart and reconfirm your order."))


class ConfirmPhase(CheckoutPhaseViewMixin, FormView):
    identifier = "confirm"
    title = _("Confirmation")

    template_name = "shuup/front/checkout/confirm.jinja"
    form_class = ConfirmForm

    def process(self):
        self.basket.customer_comment = self.storage.get("comment")
        self.basket.marketing_permission = self.storage.get("marketing")

    def is_valid(self):
        return bool(self.storage.get("accept_terms"))

    def _get_product_ids(self):
        return [str(product_id) for product_id in self.basket.get_product_ids_and_quantities().keys()]

    def get_form_kwargs(self):
        kwargs = super(ConfirmPhase, self).get_form_kwargs()
        kwargs["current_product_ids"] = set(self._get_product_ids())
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ConfirmPhase, self).get_context_data(**kwargs)
        basket = self.basket

        basket.calculate_taxes()
        errors = list(basket.get_validation_errors())
        context["basket"] = basket
        context["errors"] = errors
        context["orderable"] = (not errors)
        context["product_ids"] = ','.join(self._get_product_ids())
        return context

    def form_valid(self, form):
        for key, value in form.cleaned_data.items():
            self.storage[key] = value
        self.process()
        order = self.create_order()
        self.checkout_process.complete()  # Inform the checkout process it's completed

        if order.require_verification:
            response = redirect("shuup:order_requires_verification", pk=order.pk, key=order.key)
        else:
            response = redirect("shuup:order_process_payment", pk=order.pk, key=order.key)

        self._handle_gdpr(form, order, response)
        return response

    def _handle_gdpr(self, form, order, response):
        # create the consent for all documents and for all required cookies if user has accepted terms

        if not form.cleaned_data.get("accept_terms") or not has_installed("shuup.gdpr"):
            return

        from shuup.gdpr.models import GDPRCookieCategory, GDPRSettings, GDPRUserConsent
        from shuup.gdpr.utils import add_consent_to_response_cookie, get_cookie_consent_data

        if not GDPRSettings.get_for_shop(order.shop).enabled:
            return

        user = self.request.user
        cookies = []
        cookie_categories = []
        consent_documents = []

        # check whether there is already a consent in the request Cookie
        if settings.SHUUP_GDPR_CONSENT_COOKIE_NAME in self.request.COOKIES:
            try:
                from shuup.gdpr.utils import get_consent_from_cookie
                cookie_data = json.loads(self.request.COOKIES[settings.SHUUP_GDPR_CONSENT_COOKIE_NAME])
                cookies, cookie_categories, consent_documents = get_consent_from_cookie(cookie_data)
            except:
                logger.exception("Failed to parse GDPR from cookie")

        if not cookie_categories:
            cookie_categories = list(GDPRCookieCategory.objects.filter(shop=order.shop, always_active=True))

        if not consent_documents and has_installed("shuup.simple_cms"):
            from shuup.simple_cms.models import Page, PageType
            consent_documents = list(
                Page.objects.visible(order.shop).filter(page_type=PageType.GDPR_CONSENT_DOCUMENT))

        if user.is_authenticated():
            GDPRUserConsent.create_for_user(user, order.shop, cookie_categories, consent_documents, cookies)

        cookie_data = get_cookie_consent_data(cookie_categories, consent_documents, cookies)
        add_consent_to_response_cookie(response, cookie_data)

    def create_order(self):
        basket = self.basket
        assert basket.shop == self.request.shop
        basket.orderer = self.request.person
        basket.customer = self.request.customer
        basket.creator = self.request.user
        if "impersonator_user_id" in self.request.session:
            basket.creator = get_user_model().objects.get(pk=self.request.session["impersonator_user_id"])
        basket.status = OrderStatus.objects.get_default_initial()
        order_creator = get_basket_order_creator()
        order = order_creator.create_order(basket)
        basket.finalize()
        return order
