# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0003_category_products'),
        ('shuup', '0004_update_orderline_refunds'),
        ('shuup_testing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UltraFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='campaigns.CatalogFilter', on_delete=models.CASCADE)),
                ('categories', models.ManyToManyField(related_name='ultrafilter2', to='shuup.Category')),
                ('category', models.ForeignKey(related_name='ultrafilte5', to='shuup.Category', on_delete=models.CASCADE, null=True)),
                ('contact', models.ForeignKey(to='shuup.Contact', on_delete=models.CASCADE, null=True)),
                ('derp', models.ForeignKey(related_name='ultrafilte55', to='shuup.Category', on_delete=models.CASCADE, null=True)),
                ('product', models.ForeignKey(to='shuup.Product', on_delete=models.CASCADE, null=True)),
                ('product_type', models.ForeignKey(to='shuup.ProductType', on_delete=models.CASCADE, null=True)),
                ('product_types', models.ManyToManyField(related_name='ultrafilter3', to='shuup.ProductType')),
                ('products', models.ManyToManyField(related_name='ultrafilter1', to='shuup.Product')),
                ('shop_product', models.ForeignKey(to='shuup.ShopProduct', on_delete=models.CASCADE, null=True)),
                ('shop_products', models.ManyToManyField(related_name='ultrafilter4', to='shuup.ShopProduct')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter',),
        ),
    ]
