# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.transaction import atomic
from django.http import HttpResponseRedirect
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shuup import configuration
from shuup.admin.views.wizard import TemplatedWizardFormDef, WizardPane
from shuup.core.models import Category, Product, Shop
from shuup.testing.modules.sample_data import manager as sample_manager
from shuup.testing.modules.sample_data.data import BUSINESS_SEGMENTS
from shuup.testing.modules.sample_data.factories import (
    create_sample_carousel, create_sample_category, create_sample_product
)
from shuup.testing.modules.sample_data.forms import (
    ConsolidateObjectsForm, SampleObjectsWizardForm
)


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

        # uninstall products
        if form.cleaned_data.get("products", False):
            for product in Product.objects.filter(pk__in=sample_manager.get_installed_products(shop)):
                product.soft_delete()

        # uninstall categories
        if form.cleaned_data.get("categories", False):
            for category in Category.objects.filter(pk__in=sample_manager.get_installed_categories(shop)):
                category.soft_delete()

        # uninstall carousel
        if 'shuup.front.apps.carousel' in settings.INSTALLED_APPS and \
                form.cleaned_data.get("carousel", False):
            carousel = sample_manager.get_installed_carousel(shop)
            if carousel:
                from shuup.front.apps.carousel.models import Carousel
                Carousel.objects.filter(pk=carousel).delete()

        sample_manager.clear_installed_samples(shop)
        messages.success(self.request, _("Sample data were consolidated."))
        return HttpResponseRedirect(reverse("shuup_admin:dashboard"))

    def get_form_kwargs(self):
        kwargs = super(ConsolidateSampleObjectsView, self).get_form_kwargs()
        kwargs.update({"shop": Shop.objects.first()})
        return kwargs

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

    def valid(self):
        from shuup.admin.utils.permissions import has_permission
        return has_permission(self.request.user, "sample_data")

    def get_form_defs(self):
        return [
            TemplatedWizardFormDef(
                name="sample",
                form_class=SampleObjectsWizardForm,
                template_name="shuup/admin/sample_data/wizard.jinja",
                kwargs={
                    "shop": self.object
                }
            )
        ]

    @atomic
    def form_valid(self, form):
        current_language = translation.get_language()
        default_language = getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE", None)

        # change the language to the PARLER_DEFAULT_LANGUAGE
        # so sample data will have data on fallback languages
        if default_language:
            translation.activate(default_language)

        shop = self.object
        form_data = form["sample"].cleaned_data
        business_segment = form_data["business_segment"]

        current_categories = sample_manager.get_installed_categories(shop)
        current_products = sample_manager.get_installed_products(shop)
        current_carousel = sample_manager.get_installed_carousel(shop)

        # only saves the business segment if there is no data installed
        # otherwise user can't change the segment
        if sample_manager.has_installed_samples(shop):
            business_segment = sample_manager.get_installed_business_segment(shop)
        else:
            sample_manager.save_business_segment(shop, business_segment)

        # user wants to install sample categories
        if form_data.get("categories", False) and not current_categories:
            categories = self._create_sample_categories(shop, business_segment)
            if categories:
                sample_manager.save_categories(shop, categories)

        # user wants to install sample products
        if form_data.get("products", False) and not current_products:
            products = self._create_sample_products(shop, business_segment)
            if products:
                sample_manager.save_products(shop, products)

        # user wants a carousel
        if form_data.get("carousel") and not current_carousel:
            carousel = self._create_sample_carousel(shop, business_segment)
            if carousel:
                sample_manager.save_carousel(shop, carousel.pk)

        # back to current language
        translation.activate(current_language)

        # user will no longer see this pane
        configuration.set(None, "sample_data_wizard_completed", True)

    @classmethod
    def _create_sample_categories(cls, shop, business_segment):
        """
        Create the categories for the given business segment.
        """
        if business_segment not in BUSINESS_SEGMENTS:
            return None

        categories = []

        for category_data in BUSINESS_SEGMENTS[business_segment]["categories"]:
            category = create_sample_category(category_data["name"],
                                              category_data["description"],
                                              business_segment,
                                              category_data["image"],
                                              shop)
            categories.append(category.pk)

        return categories

    @classmethod
    def _create_sample_products(cls, shop, business_segment):
        """
        Create the sample products for the given business_segment.
        """
        if business_segment not in BUSINESS_SEGMENTS:
            return None

        products = []

        for product_data in BUSINESS_SEGMENTS[business_segment]["products"]:
            product = create_sample_product(product_data["name"],
                                            product_data["description"],
                                            business_segment,
                                            product_data["image"],
                                            shop)
            products.append(product.pk)

        return products

    @classmethod
    def _create_sample_carousel(cls, shop, business_segment):
        """
        Create the sample carousel for the given business_segment
        and also injects it to the default theme currently being used in front.
        """
        if business_segment not in BUSINESS_SEGMENTS:
            return None

        carousel_data = BUSINESS_SEGMENTS[business_segment]["carousel"]
        carousel = create_sample_carousel(carousel_data, business_segment, shop)

        # injects the carousel plugin with in the front_content placeholder
        # this will only works if the theme have this placeholder, we expect so
        if 'shuup.xtheme' in settings.INSTALLED_APPS:
            from shuup.front.apps.carousel.plugins import CarouselPlugin
            from shuup.xtheme.plugins.products import ProductHighlightPlugin

            from shuup.xtheme.models import SavedViewConfig, SavedViewConfigStatus
            from shuup.xtheme.layout import Layout
            from shuup.xtheme._theme import get_current_theme

            theme = get_current_theme(shop)

            if theme:
                layout = Layout(theme, "front_content")

                # adds the carousel
                layout.begin_row()
                layout.begin_column({"md": 12})
                layout.add_plugin(CarouselPlugin.identifier, {"carousel": carousel.pk})

                # adds some products
                layout.begin_row()
                layout.begin_column({"md": 12})
                layout.add_plugin(ProductHighlightPlugin.identifier, {})

                svc = SavedViewConfig(
                    theme_identifier=theme.identifier,
                    shop=shop,
                    view_name="IndexView",
                    status=SavedViewConfigStatus.CURRENT_DRAFT
                )
                svc.set_layout_data(layout.placeholder_name, layout)
                svc.save()
                svc.publish()

        return carousel
