# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0025_add_codes_for_order'),
        ('campaigns', '0006_effects'),
    ]

    operations = [
        migrations.CreateModel(
            name='FreeProductLine',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(primary_key=True, serialize=False, auto_created=True, to='campaigns.BasketDiscountEffect', parent_link=True)),
                ('products', models.ManyToManyField(verbose_name='product', to='shoop.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect',),
        ),
    ]
