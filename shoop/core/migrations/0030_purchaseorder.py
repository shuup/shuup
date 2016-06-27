# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0029_update_order_phone_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseOrder',
            fields=[
                ('order_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.Order')),
                ('manufacturer', models.ForeignKey(related_name='purchase_orders', on_delete=django.db.models.deletion.PROTECT, verbose_name='manufacturer', to='shoop.Manufacturer')),
            ],
            options={
                'ordering': ('-id',),
                'verbose_name': 'purchase order',
                'verbose_name_plural': 'purchase orders',
            },
            bases=('shoop.order',),
        ),
    ]
