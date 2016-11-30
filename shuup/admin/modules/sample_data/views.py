# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import os

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.transaction import atomic
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, View

from shuup import configuration
from shuup.admin.modules.sample_data import manager as sample_manager
from shuup.admin.modules.sample_data import SAMPLE_IMAGES_BASE_DIR
from shuup.admin.modules.sample_data.data import BUSINESS_SEGMENTS, CMS_PAGES
from shuup.admin.modules.sample_data.factories import (
    create_sample_category, create_sample_product
)
from shuup.admin.modules.sample_data.forms import (
    ConsolidateObjectsForm, SampleObjectsWizardForm
)
from shuup.admin.views.wizard import TemplatedWizardFormDef, WizardPane
from shuup.core.models import Category, Product, Shop


class ClearSampleObjectsView(View):
    """
    This view will clear all the installed samples no matter what.
    """

    @atomic
    def post(self, request, *args, **kwargs):
        # there would be only sample data for single-shops envs
        shop = Shop.objects.first()

        # delete categories
        for c in Category.objects.filter(pk__in=sample_manager.get_installed_categories(shop)):
            c.soft_delete()

        # delete Products
        for p in Product.objects.filter(pk__in=sample_manager.get_installed_products(shop)):
            p.soft_delete()

        # delete CMS pages
        if 'shuup.simple_cms' in settings.INSTALLED_APPS:
            from shuup.simple_cms.models import Page
            Page.objects.filter(identifier__in=sample_manager.get_installed_cms_pages(shop)).delete()

        # clear the samples from config
        sample_manager.clear_installed_samples(shop)
        messages.success(request, _("All sample data were deleted"))
        return HttpResponseRedirect(reverse("shuup_admin:dashboard"))


class ConsolidateSampleObjectsView(FormView):
    """
    This view will consolidate all the samples selected by user.
    All samples which are not in the form will be deleted.
    """

    form_class = ConsolidateObjectsForm
    template_name = "shuup/admin/sample_data/consolidate_samples.jinja"

    @atomic
    def form_valid(self, form):
        # there would be only sample data for single-shops envs
        shop = Shop.objects.first()

        products = [int(p) for p in form.cleaned_data.get("products", [])]
        categories = [int(c) for c in form.cleaned_data.get("categories", [])]

        # remove all unecessary products
        remove_products = [
            prod for prod in sample_manager.get_installed_products(shop) if prod not in products
        ]
        for p in Product.objects.filter(pk__in=remove_products):
            p.soft_delete()

        # remove all unecessary categories
        remove_categories = [
            cat for cat in sample_manager.get_installed_categories(shop) if cat not in categories
        ]
        for c in Category.objects.filter(pk__in=remove_categories):
            c.soft_delete()

        # remove all unecessary CMS pages
        if 'shuup.simple_cms' in settings.INSTALLED_APPS:
            from shuup.simple_cms.models import Page
            cms_pages = form.cleaned_data.get("cms", [])
            remove_pages = [
                page for page in sample_manager.get_installed_cms_pages(shop) if page not in cms_pages
            ]
            Page.objects.filter(identifier__in=remove_pages).delete()

        sample_manager.clear_installed_samples(shop)
        messages.success(self.request, _("Sample data were consolidated"))
        return HttpResponseRedirect(reverse("shuup_admin:dashboard"))

    def get_form_kwargs(self):
        kwargs = super(ConsolidateSampleObjectsView, self).get_form_kwargs()
        kwargs.update({"shop": Shop.objects.first()})
        return kwargs

    def get_initial(self):
        shop = Shop.objects.first()
        return {
            "products": sample_manager.get_installed_products(shop),
            "categories": sample_manager.get_installed_categories(shop),
            "cms": sample_manager.get_installed_cms_pages(shop)
        }

    def get_context_data(self, **kwargs):
        shop = Shop.objects.first()
        context = super(ConsolidateSampleObjectsView, self).get_context_data(**kwargs)
        context["has_installed_sample"] = sample_manager.has_installed_samples(shop)
        context["title"] = _("Sample Data")
        return context


class SampleObjectsWizardPane(WizardPane):
    identifier = "sample"
    icon = "shuup_admin/img/configure.png"
    title = _("Sample Data")
    text = _("To start shopping right now, please install some sample data into your shop")

    def visible(self):
        return not configuration.get(None, "sample_data_wizard_completed", False)

    def get_form_defs(self):
        return [
            TemplatedWizardFormDef(
                name="sample",
                form_class=SampleObjectsWizardForm,
                template_name="shuup/admin/sample_data/wizard.jinja"
            )
        ]

    @atomic
    def form_valid(self, form):
        shop = self.object
        form_data = form["sample"].cleaned_data
        business_segment = form_data["business_segment"]

        # user wants to install sample categories
        if form_data.get("categories", False):
            categories = self._create_sample_categories(shop, business_segment)

            if categories:
                current_categories = sample_manager.get_installed_categories(shop)
                # Merge categories with existing ones
                merged_categories = list(set(categories) | set(current_categories))
                sample_manager.save_categories(shop, merged_categories)

        # user wants to install sample products
        if form_data.get("products", False):
            products = self._create_sample_products(shop, business_segment)
            if products:
                current_products = sample_manager.get_installed_categories(shop)
                # merge the new products with the existing ones
                merged_products = list(set(products) | set(current_products))
                sample_manager.save_products(shop, merged_products)

        # user wants to install sample CMS Pages
        if form_data.get("cms"):
            cms_pages = self._create_sample_cms_pages(form_data["cms"])
            if cms_pages:
                # merge the new cms pages with the existing ones
                current_cms_pages = sample_manager.get_installed_cms_pages(shop)
                merged_pages = list(set(cms_pages) | set(current_cms_pages))
                sample_manager.save_cms_pages(shop, merged_pages)

        # user will no longer see this pane
        configuration.set(None, "sample_data_wizard_completed", True)

    def _create_sample_categories(self, shop, business_segment):
        """
        Create the categories for the given business segment
        """
        if business_segment not in BUSINESS_SEGMENTS:
            return None

        categories = []

        for category_data in BUSINESS_SEGMENTS[business_segment]["categories"]:
            image_path = os.path.join(SAMPLE_IMAGES_BASE_DIR, category_data["image"])
            category = create_sample_category(category_data["name"],
                                              category_data["description"],
                                              business_segment,
                                              image_path,
                                              shop)
            categories.append(category.pk)

        return categories

    def _create_sample_products(self, shop, business_segment):
        """
        Create the sample products for the given business_segment
        """
        if business_segment not in BUSINESS_SEGMENTS:
            return None

        products = []

        for product_data in BUSINESS_SEGMENTS[business_segment]["products"]:
            image_path = os.path.join(SAMPLE_IMAGES_BASE_DIR, product_data["image"])

            product = create_sample_product(product_data["name"],
                                            product_data["description"],
                                            business_segment,
                                            image_path,
                                            shop)
            products.append(product.pk)

        return products

    def _create_sample_cms_pages(self, cms_pages_ids):
        """
        Creates the sample CMS pages for the given list of identifiers.
        If a page with the same identifier already exists, nothing will be done.
        """

        # handle CMS if it is installed
        if 'shuup.simple_cms' in settings.INSTALLED_APPS:
            from shuup.simple_cms.models import Page

            for cms_identifier in cms_pages_ids:
                page, created = Page.objects.get_or_create(identifier=cms_identifier)

                if created:
                    page.visible_in_menu = True
                    page.title = CMS_PAGES[cms_identifier]["title"]
                    page.content = CMS_PAGES[cms_identifier]["content"]
                    page.url = cms_identifier
                    page.save()

        return cms_pages_ids
