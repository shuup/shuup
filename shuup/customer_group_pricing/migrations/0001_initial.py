# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shuup.utils.properties
import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CgpPrice',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('price_value', shuup.core.fields.MoneyValueField(verbose_name='price', decimal_places=9, max_digits=36)),
                ('group', models.ForeignKey(on_delete=models.CASCADE, verbose_name='contact group', to='shuup.ContactGroup')),
                ('product', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='shuup.Product', verbose_name='product')),
                ('shop', models.ForeignKey(on_delete=models.CASCADE, verbose_name='shop', to='shuup.Shop')),
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
