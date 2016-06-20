# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0027_contact_group_behavior'),
        ('campaigns', '0008_quantities'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscountFromProduct',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(primary_key=True, to='campaigns.BasketDiscountEffect', serialize=False, parent_link=True, auto_created=True)),
                ('per_line_discount', models.BooleanField(default=True, verbose_name='per line discount', help_text='Uncheck this if you want to give discount for each matched product.')),
                ('discount_amount', shoop.core.fields.MoneyValueField(blank=True, verbose_name='discount amount', decimal_places=9, max_digits=36, default=None, null=True, help_text='Flat amount of discount.')),
                ('products', models.ManyToManyField(verbose_name='product', to='shoop.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect',),
        ),
    ]
