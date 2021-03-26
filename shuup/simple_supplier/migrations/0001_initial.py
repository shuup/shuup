# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StockAdjustment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on', db_index=True)),
                ('delta', shuup.core.fields.QuantityField(default=0, decimal_places=9, verbose_name='delta', max_digits=36)),
                ('purchase_price_value', shuup.core.fields.MoneyValueField(default=0, decimal_places=9, max_digits=36)),
                ('created_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True, verbose_name='created by')),
                ('product', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='shuup.Product', verbose_name='product')),
                ('supplier', models.ForeignKey(on_delete=models.CASCADE, verbose_name='supplier', to='shuup.Supplier')),
            ],
        ),
        migrations.CreateModel(
            name='StockCount',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('logical_count', shuup.core.fields.QuantityField(editable=False, default=0, decimal_places=9, verbose_name='logical count', max_digits=36)),
                ('physical_count', shuup.core.fields.QuantityField(editable=False, default=0, decimal_places=9, verbose_name='physical count', max_digits=36)),
                ('stock_value_value', shuup.core.fields.MoneyValueField(default=0, decimal_places=9, max_digits=36)),
                ('product', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='shuup.Product', editable=False, verbose_name='product')),
                ('supplier', models.ForeignKey(on_delete=models.CASCADE, to='shuup.Supplier', editable=False, verbose_name='supplier')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='stockcount',
            unique_together=set([('product', 'supplier')]),
        ),
    ]
