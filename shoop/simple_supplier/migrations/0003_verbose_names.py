# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('simple_supplier', '0002_fk_on_delete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockadjustment',
            name='created_by',
            field=models.ForeignKey(verbose_name='created by', blank=True, null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='stockadjustment',
            name='created_on',
            field=models.DateTimeField(db_index=True, verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='stockadjustment',
            name='delta',
            field=shoop.core.fields.QuantityField(verbose_name='delta', decimal_places=9, max_digits=36, default=0),
        ),
        migrations.AlterField(
            model_name='stockadjustment',
            name='product',
            field=models.ForeignKey(verbose_name='product', related_name='+', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='stockadjustment',
            name='supplier',
            field=models.ForeignKey(verbose_name='supplier', to='shoop.Supplier'),
        ),
        migrations.AlterField(
            model_name='stockcount',
            name='logical_count',
            field=shoop.core.fields.QuantityField(verbose_name='logical count', decimal_places=9, max_digits=36, editable=False, default=0),
        ),
        migrations.AlterField(
            model_name='stockcount',
            name='physical_count',
            field=shoop.core.fields.QuantityField(verbose_name='physical count', decimal_places=9, max_digits=36, editable=False, default=0),
        ),
        migrations.AlterField(
            model_name='stockcount',
            name='product',
            field=models.ForeignKey(verbose_name='product', related_name='+', to='shoop.Product', editable=False),
        ),
        migrations.AlterField(
            model_name='stockcount',
            name='supplier',
            field=models.ForeignKey(verbose_name='supplier', to='shoop.Supplier', editable=False),
        ),
    ]
