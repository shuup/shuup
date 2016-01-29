# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0015_product_minimum_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='contact_address',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='contact address', blank=True, to='shoop.MutableAddress', null=True),
        ),
    ]
