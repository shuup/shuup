# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import os

import six
from django.db.models import ForeignKey, ManyToManyField, Q
from django.utils.text import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.permissions import has_permission
from shuup.core.models import (
    MediaFile, Product, ProductMedia, ProductMediaKind, ProductType, SalesUnit,
    ShopProduct, Supplier, TaxClass
)
from shuup.importer.exceptions import ImporterError
from shuup.importer.importing import (
    DataImporter, ImporterExampleFile, ImportMetaBase
)
from shuup.importer.utils import fold_mapping_name
from shuup.utils.properties import PriceProperty


class ProductMetaBase(ImportMetaBase):
    aliases = {
        "type": ["product_type", "producttype"],
        "tax_class": ["tax_class_name"],
        "name": ["title"],
        "keywords": ["tags"],
        "qty": ["quantity", "stock_amount", "stock_qty", "stock_quantity", "qty"],
        "suppliers": ["supplier"],
        "primary_category": ["category", "main_category"],
        "categories": ["extra_categories"],
        "media": ["media", "images"],
        "image": ["image", "main_image"],
        "manufacturer": ["mfgr"]
    }

    fields_to_skip = ["ignore", "shop_primary_image", "primary_image"]

    post_save_handlers = {
        "handle_stocks": ["qty"],
        "handle_images": ["image", "media"]
    }

    def _handle_image(self, shop, product, image_source, is_primary=False):
        product_media = None
        img_path, img_name = os.path.split(image_source)

        # fetch all images that are candidates using the file name
        images_candidate = list(MediaFile.objects.filter(
            Q(shops=shop),
            Q(file__original_filename__iexact=img_name) | Q(file__name__iexact=img_name)
        ).distinct())

        image = None

        if not images_candidate:
            return None

        if img_path:
            for image_candidate in images_candidate:
                # if there is any path in the image_source string,
                # we should compare that with the Filer file logical path
                # this enable users to use the 'folder1/folder2/image.jpeg' as image source
                folder_paths = image_candidate.file.logical_path
                logical_path = os.path.join(*[f.name for f in folder_paths]).lower()
                if logical_path.endswith(img_path.lower()):
                    image = image_candidate
                    break
        else:
            # just use the first one
            image = images_candidate[0]

        if image:
            product_media = ProductMedia.objects.filter(product=product, file=image.file, shops=shop).first()
            if not product_media:
                product_media = ProductMedia(
                    product=product,
                    kind=ProductMediaKind.IMAGE,
                    enabled=True,
                    public=True,
                    file=image.file
                )

        if product_media:
            product_media.full_clean()
            product_media.save()
            product_media.shops.add(shop)

            if is_primary:
                product.primary_image = product_media
                product.save(update_fields=["primary_image"])

        return product_media

    def handle_images(self, fields, sess):
        """
        Handle images for product.
        """
        # convert all keys to lowercase
        row = {k.lower(): v for k, v in sess.row.items()}
        product = sess.instance

        for image_field in self.aliases["image"]:
            image = row.get(image_field)
            if image and not self._handle_image(sess.shop, product, row[image_field], is_primary=True):
                msg = _("Image '%s' was not found, please check whether the image exists.") % row[image_field]
                sess.log_messages.append(msg)

        for image_field in self.aliases["media"]:
            images = row.get(image_field)
            if images:
                for image_source in images.split(","):
                    if not self._handle_image(sess.shop, product, image_source):
                        msg = _("Image '%s' was not found, please check whether the image exists.") % image_source
                        sess.log_messages.append(msg)

        # check whether the product has media but doesn't have a primary image
        # set the first available media as primary
        product_medias = ProductMedia.objects.filter(product=product, shops=sess.shop)
        if not product.primary_image and product_medias.exists():
            product.primary_image = product_medias.first()
            product.save()

    def handle_stocks(self, fields, sess):
        """
        Handle stocks for product.

        If stock quantity has been given, expect that a supplier with stock management must be available.
        """
        # convert all keys to lowercase
        row = {k.lower(): v for k, v in sess.row.items()}

        # check if row even has these fields we are requiring
        field_found = False
        for qty_field in self.aliases["qty"]:
            if qty_field in row:
                field_found = True
                break

        if not field_found:  # no need to process this as qty was not available
            return

        supplier_id = row.get("supplier")
        if not supplier_id:
            raise ImporterError(_("Please add supplier to the row, before importing stock quantities."))
        # shuup only has 1 supplier support now so get first
        supplier = sess.importer.resolve_object(Supplier, supplier_id)
        if not supplier:
            raise ImporterError(_("No supplier found, please check that the supplier exists."))
        if not supplier.stock_managed:
            raise ImporterError(_(
                "This supplier doesn't handle stocks, please set `Stock Managed` "
                "on in the individual Supplier's settings page.")
            )

        for qty_field in self.aliases["qty"]:
            qty_field = qty_field.lower()
            val = row.get(qty_field, None)
            if val is not None:
                supplier.adjust_stock(sess.instance.pk, val)
                break

    def presave_hook(self, sess):
        # ensure tax_class id is there
        product = sess.instance
        if not product.description:
            product.description = ""

    def postsave_hook(self, sess):
        # get all the special values
        shop_product = ShopProduct.objects.get_or_create(product=sess.instance, shop=sess.shop)[0]

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

        # add shop relation to the manufacturer
        if sess.instance.manufacturer:
            sess.instance.manufacturer.shops.add(sess.shop)

        # add shop relation to all categories
        for category in shop_product.categories.all():
            category.shops.add(sess.shop)

    def _find_related_values(self, field_name, sess, value):
        is_related_field = False
        field_mapping = sess.importer.mapping.get(field_name)

        for related_field, relmapper in sess.importer.relation_map_cache.items():
            if related_field.name != field_name:
                continue

            is_related_field = True
            if isinstance(related_field, ManyToManyField) and value is None:
                return ([], related_field)

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
        Get default values for import time.
        """
        data = {
            "type_id": ProductType.objects.first().pk,
            "tax_class_id": TaxClass.objects.first().pk,
            "sales_unit_id": SalesUnit.objects.first().pk
        }
        return data


class ProductImporter(DataImporter):
    identifier = "product_importer"
    name = _("Product Importer")
    meta_base_class = ProductMetaBase
    model = Product
    relation_field = "product"
    help_template = "shuup/default_importers/product_help.jinja"

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
            "product_sample_import_with_images.xlsx",
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

    @classmethod
    def get_help_context_data(cls, request):
        from shuup.admin.shop_provider import get_shop
        return {
            "has_media_browse_permission": has_permission(request.user, "media.browse"),
            "supplier": Supplier.objects.enabled().filter(shops=get_shop(request)).first()
        }
