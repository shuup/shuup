# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import shuup.core.fields
import shuup.utils.properties


class Migration(migrations.Migration):

    replaces = [
        ('shuup_customer_group_pricing', '0001_initial'),
        ('shuup_customer_group_pricing', '0002_discounts'),
    ]

    dependencies = [
        ('shuup', '0001_squashed_0039_alter_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='CgpPrice',
            fields=[
                ('id', models.AutoField(
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                    auto_created=True)),
                ('price_value', shuup.core.fields.MoneyValueField(
                    max_digits=36, decimal_places=9, verbose_name='price')),
                ('group', models.ForeignKey(on_delete=models.CASCADE,
                    to='shuup.ContactGroup', verbose_name='contact group')),
                ('product', models.ForeignKey(on_delete=models.CASCADE,
                    related_name='+',
                    verbose_name='product',
                    to='shuup.Product')),
                ('shop', models.ForeignKey(on_delete=models.CASCADE,
                    to='shuup.Shop', verbose_name='shop')),
            ],
            options={
                'verbose_name_plural': 'product prices',
                'verbose_name': 'product price',
            },
            bases=(shuup.utils.properties.MoneyPropped, models.Model), ),
        migrations.AlterUniqueTogether(
            name='cgpprice',
            unique_together=set([('product', 'shop', 'group')]), ),
        migrations.CreateModel(
            name='CgpDiscount',
            fields=[
                ('id', models.AutoField(
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                    auto_created=True)),
                ('discount_amount_value', shuup.core.fields.MoneyValueField(
                    max_digits=36,
                    decimal_places=9,
                    verbose_name='discount amount')),
                ('group', models.ForeignKey(on_delete=models.CASCADE,
                    to='shuup.ContactGroup', verbose_name='contact group')),
                ('product', models.ForeignKey(on_delete=models.CASCADE,
                    related_name='+',
                    verbose_name='product',
                    to='shuup.Product')),
                ('shop', models.ForeignKey(on_delete=models.CASCADE,
                    to='shuup.Shop', verbose_name='shop')),
            ],
            options={
                'verbose_name_plural': 'product discounts',
                'abstract': False,
                'verbose_name': 'product discount',
            },
            bases=(shuup.utils.properties.MoneyPropped, models.Model), ),
        migrations.AlterUniqueTogether(
            name='cgpdiscount',
            unique_together=set([('product', 'shop', 'group')]), ),
    ]
