# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.db.models import ForeignKey
from django.utils.text import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import (
    Product, ProductType, ShopProduct, Supplier, TaxClass
)
from shuup.importer.exceptions import ImporterError
from shuup.importer.importing import (
    DataImporter, ImporterExampleFile, ImportMetaBase
)
from shuup.importer.utils import fold_mapping_name
from shuup.simple_supplier.models import StockAdjustment
from shuup.utils.properties import PriceProperty


class ProductMetaBase(ImportMetaBase):
    aliases = {
        "type": ["product_type", "producttype"],
        "tax_class": ["tax_class_name"],
        "name": ["title"],
        "keywords": ["tags"],
        "qty": ["quantity", "stock_amount", "stock_qty", "stock_quantity"],
        "suppliers": ["supplier"],
        "primary_category": ["category", "main_category"],
        "categories": ["extra_categories"],
        "manufacturer": ["mfgr"]
    }

    fields_to_skip = ["shop_primary_image", "primary_image"]

    post_save_handlers = {
        "handle_stocks": ["qty"],
    }

    def handle_stocks(self, fields, sess):
        """
        Handle stocks for product

        If stock qty has been given, expect that a supplier with stock management must be available.
        """
        row = sess.row

        # check if row even has these fields we are requiring
        field_found = False
        for qty_field in self.aliases["qty"]:
            if qty_field in row:
                field_found = True
                break

        if not field_found:  # no need to process this as qty was not available
            return

        supplier = row.get("supplier")
        if not supplier:
            raise ImporterError(_("Please add supplier to row before importing stock quantities."))
        # shuup only has 1 supplier support now so get first
        obj = sess.importer.resolve_object(Supplier, supplier)
        if not obj:
            raise ImporterError(_("No supplier found, please check the supplier exists."))
        if not obj.stock_managed:
            raise ImporterError(_("This supplier doesn't handle stocks, please set Stock Managed on."))

        for qty_field in self.aliases["qty"]:
            val = row.get(qty_field, None)
            if val is not None:
                StockAdjustment(product=sess.instance, delta=val)
                break

    def presave_hook(self, sess):
        # ensure tax_class id is there
        product = sess.instance
        if not product.description:
            product.description = ""

    def postsave_hook(self, sess):
        # get all the special values

        try:
            shop_product = ShopProduct.objects.get(product=sess.instance)
        except:
            shop_product = ShopProduct()

        shop_product.shop = sess.shop
        shop_product.product = sess.instance
        shop_product.save()

        matched_fields = []
        for k, v in six.iteritems(sess.importer.extra_matches):
            if k.startswith("ShopProduct:"):
                x, field = k.split(":")
                matched_fields.append(field)
                val = sess.row.get(v)
                setattr(shop_product, field, val)

        for k, v in sess.importer.data_map.items():
            field_name = v.get("id")
            if field_name in self.fields_to_skip:
                continue
            if hasattr(shop_product, field_name):
                field = getattr(shop_product, field_name)
                value = sess.row.get(k, None)

                if isinstance(field, PriceProperty):
                    value = sess.shop.create_price(value)

                value, is_related = self._find_related_values(field_name, sess, value)
                if is_related and isinstance(value, six.string_types):
                    continue

                setattr(shop_product, field_name, value)
        shop_product.save()

    def _find_related_values(self, field_name, sess, value):
        is_related_field = False
        if not value:
            return (value, is_related_field)

        field_mapping = sess.importer.mapping.get(field_name)

        for related_field, relmapper in sess.importer.relation_map_cache.items():
            if related_field.name != field_name:
                continue

            is_related_field = True
            if isinstance(related_field, ForeignKey):
                try:
                    value = int(value)  # this is because xlrd causes 1 to be 1.0
                except:
                    pass
                value = relmapper.fk_cache.get(str(value))
                break
            else:
                value = sess.importer.relation_map_cache.get(field_mapping.get("field")).map_cache[value]
                break

        if field_mapping.get("is_enum_field"):
            field = field_mapping.get("field")
            for k, v in field.get_choices():
                if fold_mapping_name(force_text(v)) == fold_mapping_name(value):
                    value = k
                    break
        return (value, is_related_field)

    def get_import_defaults(self):
        """
        Get default values for import time
        """
        data = {
            "type_id": ProductType.objects.first().id,
            "tax_class_id": TaxClass.objects.first().id,
        }
        return data


class ProductImporter(DataImporter):
    identifier = "product_importer"
    name = _("Product Importer")
    meta_base_class = ProductMetaBase
    model = Product
    relation_field = "product"

    def get_related_models(self):
        return [Product, ShopProduct]

    example_files = [
        ImporterExampleFile(
            "product_sample_import.xls",
            ("application/vnd.ms-excel", "application/excel")
        ),
        ImporterExampleFile(
            "product_sample_import.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        ImporterExampleFile(
            "product_sample_complex_import.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        ImporterExampleFile(
            "product_sample_import.csv",
            "text/csv"
        )
    ]

    @classmethod
    def get_example_file_content(cls, example_file, request):
        from shuup.default_importer.samples import get_sample_file_content
        return get_sample_file_content(example_file.file_name)
