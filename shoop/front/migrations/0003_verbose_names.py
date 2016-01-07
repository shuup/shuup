# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import shoop.core.fields
import shoop.front.models.stored_basket


class Migration(migrations.Migration):

    dependencies = [
        ('shoop_front', '0002_tax_price_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storedbasket',
            name='created_on',
            field=models.DateTimeField(db_index=True, verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='creator',
            field=models.ForeignKey(verbose_name='creator', blank=True, null=True, related_name='baskets_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='currency',
            field=shoop.core.fields.CurrencyField(verbose_name='currency', max_length=4),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='customer',
            field=models.ForeignKey(verbose_name='customer', blank=True, null=True, related_name='customer_baskets', to='shoop.Contact'),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='data',
            field=shoop.core.fields.TaggedJSONField(verbose_name='data'),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='deleted',
            field=models.BooleanField(db_index=True, verbose_name='deleted', default=False),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='finished',
            field=models.BooleanField(db_index=True, verbose_name='finished', default=False),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='key',
            field=models.CharField(verbose_name='key', max_length=32, default=shoop.front.models.stored_basket.generate_key),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='orderer',
            field=models.ForeignKey(verbose_name='orderer', blank=True, null=True, related_name='orderer_baskets', to='shoop.PersonContact'),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='persistent',
            field=models.BooleanField(db_index=True, verbose_name='persistent', default=False),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='prices_include_tax',
            field=models.BooleanField(verbose_name='prices include tax'),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='product_count',
            field=models.IntegerField(verbose_name='product_count', default=0),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='products',
            field=models.ManyToManyField(verbose_name='products', blank=True, to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='shop',
            field=models.ForeignKey(verbose_name='shop', to='shoop.Shop'),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='taxful_total_price_value',
            field=shoop.core.fields.MoneyValueField(max_digits=36, blank=True, null=True, verbose_name='taxful total price', decimal_places=9, default=0),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='taxless_total_price_value',
            field=shoop.core.fields.MoneyValueField(max_digits=36, blank=True, null=True, verbose_name='taxless total price', decimal_places=9, default=0),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='title',
            field=models.CharField(verbose_name='title', blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='updated_on',
            field=models.DateTimeField(db_index=True, verbose_name='updated on', auto_now=True),
        ),
    ]
