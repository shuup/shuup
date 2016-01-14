# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.models._shops
import shoop.core.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0009_tax_price_currency'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shoop_front', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='storedbasket',
            old_name='taxful_total',
            new_name='taxful_total_price_value',
        ),
        migrations.RenameField(
            model_name='storedbasket',
            old_name='taxless_total',
            new_name='taxless_total_price_value',
        ),
        migrations.RenameField(
            model_name='storedbasket',
            old_name='owner_contact',
            new_name='customer',
        ),
        migrations.RenameField(
            model_name='storedbasket',
            old_name='owner_user',
            new_name='creator',
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='creator',
            field=models.ForeignKey(null=True, related_name='baskets_created', blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='storedbasket',
            name='currency',
            field=shoop.core.fields.CurrencyField(max_length=4, default=shoop.core.models._shops._get_default_currency),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='customer',
            field=models.ForeignKey(null=True, related_name='customer_baskets', blank=True, to='shoop.Contact'),
        ),
        migrations.AddField(
            model_name='storedbasket',
            name='orderer',
            field=models.ForeignKey(null=True, related_name='orderer_baskets', blank=True, to='shoop.PersonContact'),
        ),
        migrations.AddField(
            model_name='storedbasket',
            name='prices_include_tax',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='storedbasket',
            name='shop',
            field=models.ForeignKey(to='shoop.Shop', default=1),
            preserve_default=False,
        ),
    ]
