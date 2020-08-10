# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
import enumfields.fields
from django.conf import settings
from django.db import migrations, models

import shuup.core.fields
import shuup.core.suppliers.enums


class Migration(migrations.Migration):
    replaces = [
        ('simple_supplier', '0001_initial'),
        ('simple_supplier', '0002_stockadjustment_type'),
        ('simple_supplier', '0003_stockcount_alert_limit'),
    ]

    dependencies = [
        ('shuup', '0001_squashed_0039_alter_names'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StockAdjustment',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID',
                    serialize=False,
                    primary_key=True,
                    auto_created=True)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on',
                    db_index=True,
                    auto_now_add=True)),
                ('delta', shuup.core.fields.QuantityField(
                    verbose_name='delta',
                    max_digits=36,
                    decimal_places=9,
                    default=0)),
                ('purchase_price_value', shuup.core.fields.MoneyValueField(
                    max_digits=36, decimal_places=9, default=0)),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    blank=True,
                    verbose_name='created by',
                    to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(
                    on_delete=models.CASCADE,
                    verbose_name='product',
                    to='shuup.Product',
                    related_name='+')),
                ('supplier', models.ForeignKey(
                    on_delete=models.CASCADE, verbose_name='supplier', to='shuup.Supplier')),
                ('type', enumfields.fields.EnumIntegerField(
                    enum=shuup.core.suppliers.enums.StockAdjustmentType,
                    verbose_name='type',
                    db_index=True,
                    default=1)),
            ], ),
        migrations.CreateModel(
            name='StockCount',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID',
                    serialize=False,
                    primary_key=True,
                    auto_created=True)),
                ('logical_count', shuup.core.fields.QuantityField(
                    verbose_name='logical count',
                    max_digits=36,
                    editable=False,
                    decimal_places=9,
                    default=0)),
                ('physical_count', shuup.core.fields.QuantityField(
                    verbose_name='physical count',
                    max_digits=36,
                    editable=False,
                    decimal_places=9,
                    default=0)),
                ('stock_value_value', shuup.core.fields.MoneyValueField(
                    max_digits=36, decimal_places=9, default=0)),
                ('product', models.ForeignKey(
                    on_delete=models.CASCADE,
                    editable=False,
                    verbose_name='product',
                    to='shuup.Product',
                    related_name='+')),
                ('supplier', models.ForeignKey(
                    on_delete=models.CASCADE,
                    editable=False,
                    verbose_name='supplier',
                    to='shuup.Supplier')),
                ('alert_limit', shuup.core.fields.QuantityField(
                    verbose_name='alert limit',
                    max_digits=36,
                    editable=False,
                    decimal_places=9,
                    default=0)),
            ], ),
        migrations.AlterUniqueTogether(
            name='stockcount',
            unique_together=set([('product', 'supplier')])),
    ]
