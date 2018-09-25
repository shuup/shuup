# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.transaction import atomic
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView

from shuup.admin.form_part import (
    FormPart,
    FormPartsViewMixin,
    SaveFormPartsMixin,
    TemplatedFormDef
)
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.utils.form_group import FormGroup
from shuup.front.utils.views import cache_product_things
from shuup.front.template_helpers.product import is_visible
from shuup.front.utils.sorts_and_filters import (
    get_product_queryset, get_query_filters, post_filter_products,
    ProductListForm, sort_products
)
from shuup.core.models import (
    Attribute,
    Product,
    Category,
    Product,
)
from .forms import (
    BaseFilterSettingsForm,
    CategoriesFilterSettingsForm,
    AttributesFilterSettingsForm,
    ProductFilterForm,
)
from .models import (
    BasicFilterSettingsModel,
    CategoriesFilterSettingsModel,
    BasicAttributesFilterSettingsModel,
    AttributesFilterSettingsModel,
    BASIC_ATTRIBUTE_FIELDS,
    LAYOUT_CHOICES,
)


class BaseFilterSettingsFormPart(FormPart):
    priority = 1
    name = 'base_settings'
    form = BaseFilterSettingsForm

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            self.form,
            template_name='shuup/product_filter/admin/edit_base_settings_form.jinja',
            required=True,
            kwargs={
                'instance': self.object
            }
        )

    def form_valid(self, form):
        self.object = form[self.name].save()
        self.object.shop = get_shop(self.request)
        self.object.save()
        return self.object


class CategoriesFilterSettingsFormPart(FormPart):
    priority = 2
    name = 'categories_settings'
    form = CategoriesFilterSettingsForm

    def get_form_defs(self):
        try:
            instance = CategoriesFilterSettingsModel.objects.filter(
                shop=get_shop(self.request)
            ).first()
        except:
            instance = CategoriesFilterSettingsModel()
        yield TemplatedFormDef(
            self.name,
            self.form,
            template_name='shuup/product_filter/admin/edit_categories_settings_form.jinja',
            required=True,
            kwargs={
                'instance': instance,
            }
        )

    def form_valid(self, form):
        self.object = form[self.name].save()
        self.object.shop = get_shop(self.request)
        self.object.save()
        return self.object


class AttributesFilterSettingsFormPart(FormPart):
    priority = 3
    name = 'attributes_settings'
    form = AttributesFilterSettingsForm

    def get_form_defs(self):
        try:
            instance = AttributesFilterSettingsModel.objects.filter(
                shop=get_shop(self.request)
            ).first()
        except AttributesFilterSettingsModel.DoesNotExist:
            instance = AttributesFilterSettingsModel()
        yield TemplatedFormDef(
            self.name,
            self.form,
            template_name='shuup/product_filter/admin/edit_attributes_settings_form.jinja',
            required=True,
            kwargs={
                'instance': instance,
                'initial': self.get_initial(),
            }
        )

    def get_initial(self):
        try:
            objects = AttributesFilterSettingsModel.objects.filter(
                shop=get_shop(self.request)
            )
        except AttributesFilterSettingsModel.DoesNotExist:
            pass

        try:
            basic_objects = BasicAttributesFilterSettingsModel.objects.filter(
                shop=get_shop(self.request)
            )
        except BasicAttributesFilterSettingsModel.DoesNotExist:
            pass

        fields = {}
        if objects:
            for obj in objects:
                fields['enabled_%s' % (obj.attribute_id)] = obj.enabled

        if basic_objects:
            for b_obj in basic_objects:
                fields['enabled-%s' % (b_obj.attribute_name)] = b_obj.enabled

        return fields

    def form_valid(self, form):
        data = form[self.name].cleaned_data
        for key in data.keys():
            if '-' not in key:
                pk = key.split('_')[-1]
                attribute = Attribute.objects.get(id=pk)
                enabled = data['enabled_%s' % (pk)]
                filter_obj = AttributesFilterSettingsModel.objects\
                    .update_or_create(
                        attribute=attribute,
                        defaults={
                            'enabled': enabled,
                            'shop': get_shop(self.request)
                        }
                    )
            elif '-' in key:
                b_attr_name = key.split('-')[-1]
                b_enabled = data['enabled-%s' % (b_attr_name)]
                b_filter_obj = BasicAttributesFilterSettingsModel.objects\
                    .update_or_create(
                        attribute_name=b_attr_name,
                        defaults={
                            'enabled': b_enabled,
                            'shop': get_shop(self.request)
                        }
                    )


class ProductFilterSettingsView(FormPartsViewMixin, SaveFormPartsMixin,
                                CreateOrUpdateView):
    form_class = None
    template_name = 'shuup/product_filter/admin/edit.jinja'
    context_object_name = 'product_filter'
    base_form_part_classes = [
        BaseFilterSettingsFormPart,
        CategoriesFilterSettingsFormPart,
        AttributesFilterSettingsFormPart,
    ]

    def get_object(self):
        try:
            instance = BasicFilterSettingsModel.objects.get(
                shop=get_shop(self.request)
            )
        except:
            instance = BasicFilterSettingsModel()
        return instance

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)

    def get_success_url(self):
        return reverse('shuup_admin:product_filter.list')


class ProductFilterView(ListView):
    form_class = ProductListForm
    template_name = 'shuup/product_filter/front/product_filter.jinja'
    model = Product
    context_object_name = 'products'

    def dispatch(self, request, *args, **kwargs):
        self.form = ProductListForm(
            request=self.request,
            shop=self.request.shop,
            category=None,
            data=self.request.GET
        )
        return super(ProductFilterView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if not self.form.is_valid():
            return Product.objects.none()
        data = self.form.cleaned_data
        if not data:  # pragma: no cover
            return Product.objects.none()
        products = Product.objects.filter(get_query_filters(self.request, None, data=data))
        return get_product_queryset(products, self.request, None, data)

    def get_context_data(self, **kwargs):
        context = super(ProductFilterView, self).get_context_data(**kwargs)
        context['filter_form'] = self.form
        context['layout'] = 'vertical'
        del self.form.fields['sort']
        del self.form.fields['q']

        try:
            settings = BasicFilterSettingsModel.objects.get(
                shop=get_shop(self.request),
            )
            print(settings.layout)
            context['enabled'] = settings.enabled
            if settings.layout == 1:
                context['layout'] = 'vertical'
            elif settings.layout == 2:
                context['layout'] = 'horizontal'
        except BasicFilterSettingsModel.DoesNotExist:
            raise ImproperlyConfigured(
                _('Please, define filter settings in admin backend!')
            )

        products = context['products']
        attributes = {}

        if products:
            data = self.form.cleaned_data
            products = post_filter_products(self.request, None, products, data)
            products = cache_product_things(self.request, products)
            products = sort_products(self.request, None, products, data)
            products = [p for p in products if is_visible({'request': self.request}, p)]
            context['products'] = products

        context['no_results'] = (self.form.is_valid() and not products)
        return context
