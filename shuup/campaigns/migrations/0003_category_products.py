# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import enumfields.fields
import shuup.core.fields
import shuup.campaigns.models.basket_conditions


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0002_rounding'),
        ('campaigns', '0002_productsinbasketcondition_operator'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryProductsBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(on_delete=models.CASCADE, serialize=False, auto_created=True, primary_key=True, to='campaigns.BasketCondition', parent_link=True)),
                ('operator', enumfields.fields.EnumIntegerField(verbose_name='operator', enum=shuup.campaigns.models.basket_conditions.ComparisonOperator, default=1)),
                ('quantity', models.PositiveIntegerField(verbose_name='quantity', default=1)),
                ('category', models.ForeignKey(on_delete=models.CASCADE, blank=True, null=True, to='shuup.Category', verbose_name='category')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='DiscountFromCategoryProducts',
            fields=[
                ('basketlineeffect_ptr', models.OneToOneField(on_delete=models.CASCADE, serialize=False, auto_created=True, primary_key=True, to='campaigns.BasketLineEffect', parent_link=True)),
                ('discount_amount', shuup.core.fields.MoneyValueField(null=True, decimal_places=9, blank=True, help_text='Flat amount of discount.', default=None, max_digits=36, verbose_name='discount amount')),
                ('discount_percentage', models.DecimalField(null=True, decimal_places=5, blank=True, help_text='The discount percentage for this campaign.', max_digits=6, verbose_name='discount percentage')),
                ('category', models.ForeignKey(on_delete=models.CASCADE, verbose_name='category', to='shuup.Category')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketlineeffect',),
        ),
    ]
