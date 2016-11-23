# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shuup.utils.properties
from django.conf import settings
import shuup.front.models.stored_basket
import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StoredBasket',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('key', models.CharField(verbose_name='key', max_length=32, default=shuup.front.models.stored_basket.generate_key)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on', db_index=True)),
                ('updated_on', models.DateTimeField(verbose_name='updated on', auto_now=True, db_index=True)),
                ('persistent', models.BooleanField(verbose_name='persistent', db_index=True, default=False)),
                ('deleted', models.BooleanField(verbose_name='deleted', db_index=True, default=False)),
                ('finished', models.BooleanField(verbose_name='finished', db_index=True, default=False)),
                ('title', models.CharField(verbose_name='title', max_length=64, blank=True)),
                ('data', shuup.core.fields.TaggedJSONField(verbose_name='data')),
                ('taxless_total_price_value', shuup.core.fields.MoneyValueField(blank=True, null=True, verbose_name='taxless total price', decimal_places=9, default=0, max_digits=36)),
                ('taxful_total_price_value', shuup.core.fields.MoneyValueField(blank=True, null=True, verbose_name='taxful total price', decimal_places=9, default=0, max_digits=36)),
                ('currency', shuup.core.fields.CurrencyField(max_length=4, verbose_name='currency')),
                ('prices_include_tax', models.BooleanField(verbose_name='prices include tax')),
                ('product_count', models.IntegerField(default=0, verbose_name='product_count')),
                ('creator', models.ForeignKey(blank=True, related_name='baskets_created', to=settings.AUTH_USER_MODEL, null=True, verbose_name='creator')),
                ('customer', models.ForeignKey(blank=True, related_name='customer_baskets', to='shuup.Contact', null=True, verbose_name='customer')),
                ('orderer', models.ForeignKey(blank=True, related_name='orderer_baskets', to='shuup.PersonContact', null=True, verbose_name='orderer')),
                ('products', models.ManyToManyField(blank=True, verbose_name='products', to='shuup.Product')),
                ('shop', models.ForeignKey(verbose_name='shop', to='shuup.Shop')),
            ],
            bases=(shuup.utils.properties.MoneyPropped, models.Model),
        ),
    ]
