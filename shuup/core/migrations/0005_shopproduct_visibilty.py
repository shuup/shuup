# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import enumfields.fields
from django.db import migrations, models

from shuup.core.models._product_shops import ShopProductVisibility


def shop_product_visibility(apps, schema_editor):
    ShopProduct = apps.get_model("shuup", "ShopProduct")
    for shop_product in ShopProduct.objects.all():
        listed = shop_product.listed
        searchable = shop_product.searchable
        if not (listed or searchable):
            visibility = ShopProductVisibility.NOT_VISIBLE
        elif listed and not searchable:
            visibility = ShopProductVisibility.LISTED
        elif searchable and not listed:
            visibility = ShopProductVisibility.SEARCHABLE
        else:
            visibility = ShopProductVisibility.ALWAYS_VISIBLE

        shop_product.visibility = visibility
        shop_product.save()

def reverse_shop_product_visibility(apps, schema_editor):
    ShopProduct = apps.get_model("shuup", "ShopProduct")
    for shop_product in ShopProduct.objects.all():
        visibility = shop_product.visibility
        if visibility == ShopProductVisibility.NOT_VISIBLE:
            visible = False
            listed = False
            searchable = False
        elif visibility == ShopProductVisibility.LISTED:
            visible = True
            listed = True
            searchable = False
        elif visibility == ShopProductVisibility.SEARCHABLE:
            visible = True
            listed = False
            searchable = True
        else:
            visible = True
            listed = True
            searchable = True
        shop_product.visible = visible
        shop_product.listed = listed
        shop_product.searchable = searchable
        shop_product.save()


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0004_update_orderline_refunds'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopproduct',
            name='visibility',
            field=enumfields.fields.EnumIntegerField(enum=ShopProductVisibility, db_index=True, verbose_name='visibility', default=0),
        ),
        migrations.RunPython(shop_product_visibility, reverse_code=reverse_shop_product_visibility),
        migrations.RemoveField(
            model_name='shopproduct',
            name='visible',
        ),
        migrations.RemoveField(
            model_name='shopproduct',
            name='listed',
        ),
        migrations.RemoveField(
            model_name='shopproduct',
            name='searchable',
        ),

    ]
