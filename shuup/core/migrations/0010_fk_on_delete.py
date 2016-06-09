# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shuup.core.fields
import filer.fields.image
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0009_tax_price_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='image',
            field=filer.fields.image.FilerImageField(on_delete=django.db.models.deletion.SET_NULL, to='filer.Image', null=True, blank=True, verbose_name='image'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='default_payment_method',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='shuup.PaymentMethod', null=True, blank=True, verbose_name='default payment method'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='default_shipping_method',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='shuup.ShippingMethod', null=True, blank=True, verbose_name='default shipping method'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='tax_group',
            field=models.ForeignKey(to='shuup.CustomerTaxGroup', null=True, blank=True, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='order',
            name='creator',
            field=shuup.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders_created', to=settings.AUTH_USER_MODEL, null=True, blank=True, verbose_name='creating user'),
        ),
        migrations.AlterField(
            model_name='order',
            name='customer',
            field=shuup.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='customer_orders', to='shuup.Contact', null=True, blank=True, verbose_name='customer'),
        ),
        migrations.AlterField(
            model_name='order',
            name='orderer',
            field=shuup.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orderer_orders', to='shuup.PersonContact', null=True, blank=True, verbose_name='orderer'),
        ),
        migrations.AlterField(
            model_name='order',
            name='shop',
            field=shuup.core.fields.UnsavedForeignKey(to='shuup.Shop', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=shuup.core.fields.UnsavedForeignKey(to='shuup.OrderStatus', on_delete=django.db.models.deletion.PROTECT, verbose_name='status'),
        ),
        migrations.AlterField(
            model_name='paymentmethod',
            name='tax_class',
            field=models.ForeignKey(to='shuup.TaxClass', on_delete=django.db.models.deletion.PROTECT, verbose_name='tax class'),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, help_text='only used for administration and reporting', related_name='primary_products', to='shuup.Category', blank=True, verbose_name='primary category', null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='manufacturer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shuup.Manufacturer', null=True, blank=True, verbose_name='manufacturer'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sales_unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shuup.SalesUnit', null=True, blank=True, verbose_name='unit'),
        ),
        migrations.AlterField(
            model_name='product',
            name='tax_class',
            field=models.ForeignKey(to='shuup.TaxClass', on_delete=django.db.models.deletion.PROTECT, verbose_name='tax class'),
        ),
        migrations.AlterField(
            model_name='shippingmethod',
            name='tax_class',
            field=models.ForeignKey(to='shuup.TaxClass', on_delete=django.db.models.deletion.PROTECT, verbose_name='tax class'),
        ),
        migrations.AlterField(
            model_name='shop',
            name='logo',
            field=filer.fields.image.FilerImageField(on_delete=django.db.models.deletion.SET_NULL, to='filer.Image', null=True, blank=True, verbose_name='logo'),
        ),
        migrations.AlterField(
            model_name='shop',
            name='owner',
            field=models.ForeignKey(to='shuup.Contact', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='primary_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='primary_shop_products', to='shuup.Category', null=True, blank=True, verbose_name='primary category'),
        ),
    ]
