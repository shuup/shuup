# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shuup.utils.properties
import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0015_product_minimum_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='CgpPrice',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('price_value', shuup.core.fields.MoneyValueField(max_digits=36, verbose_name='price', decimal_places=9)),
                ('group', models.ForeignKey(verbose_name='contact group', to='shuup.ContactGroup')),
                ('product', models.ForeignKey(verbose_name='product', to='shuup.Product', related_name='+')),
                ('shop', models.ForeignKey(verbose_name='shop', to='shuup.Shop')),
            ],
            options={
                'verbose_name': 'product price',
                'verbose_name_plural': 'product prices',
            },
            bases=(shuup.utils.properties.MoneyPropped, models.Model),
        ),
        migrations.AlterUniqueTogether(
            name='cgpprice',
            unique_together=set([('product', 'shop', 'group')]),
        ),
    ]
