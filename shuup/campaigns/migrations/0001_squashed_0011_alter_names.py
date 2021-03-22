# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.validators
import django.db.models.deletion
import enumfields.fields
import jsonfield.fields
import parler.models
import re
from django.conf import settings
from django.db import migrations, models

import shuup.campaigns.models.basket_conditions
import shuup.core.fields
import shuup.utils.analog
import shuup.utils.properties


class Migration(migrations.Migration):
    replaces = [
        ('campaigns', '0001_initial'),
        ('campaigns', '0002_productsinbasketcondition_operator'),
        ('campaigns', '0003_category_products'),
        ('campaigns', '0004_logmodels'),
        ('campaigns', '0005_catalogfiltercachedshopproduct'),
        ('campaigns', '0006_basket_cond_category_to_categories'),
        ('campaigns', '0007_add_excluded_categories'),
        ('campaigns', '0008_freeproductline_quantity_to_quantityfield'),
        ('campaigns', '0009_hourcondition'),
        ('campaigns', '0010_hourbasketcondition'),
        ('campaigns', '0011_alter_names'),
    ]

    dependencies = [
        ('shuup', '0001_squashed_0039_alter_names'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BasketCampaign',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('name', models.CharField(
                    help_text='The name for this campaign.',
                    max_length=120,
                    verbose_name='name')),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    editable=False,
                    blank=True,
                    max_length=64,
                    null=True,
                    unique=True)),
                ('active', models.BooleanField(
                    help_text=
                    'Check this if the campaign is currently active. Please also set a start and end date.',
                    verbose_name='active',
                    default=False)),
                ('start_datetime', models.DateTimeField(
                    blank=True,
                    help_text=
                    'The date and time the campaign starts. This is only applicable if the campaign is marked as active.',
                    null=True,
                    verbose_name='start date and time')),
                ('end_datetime', models.DateTimeField(
                    blank=True,
                    help_text=
                    'The date and time the campaign ends. This is only applicable if the campaign is marked as active.',
                    null=True,
                    verbose_name='end date and time')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    auto_now=True, verbose_name='modified on')),
                ('basket_line_text', models.CharField(
                    help_text='This text will be shown in basket.',
                    max_length=120,
                    verbose_name='basket line text')),
            ],
            options={
                'abstract': False,
                'verbose_name_plural': 'Campaigns',
                'verbose_name': 'Campaign',
            },
            bases=(shuup.utils.properties.MoneyPropped,
                   parler.models.TranslatableModelMixin, models.Model), ),
        migrations.CreateModel(
            name='BasketCampaignLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    max_length=256, verbose_name='message')),
                ('identifier', models.CharField(
                    blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(
                    enum=shuup.utils.analog.LogEntryKind,
                    verbose_name='log entry kind',
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(on_delete=models.CASCADE,
                    to='campaigns.BasketCampaign',
                    related_name='log_entries',
                    verbose_name='target')),
                ('user', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.PROTECT,
                    null=True,
                    verbose_name='user')),
            ],
            options={
                'abstract': False,
            }, ),
        migrations.CreateModel(
            name='BasketCampaignTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('language_code', models.CharField(
                    max_length=15, db_index=True, verbose_name='Language')),
                ('public_name', models.CharField(
                    help_text='The campaign name to show in the store front.',
                    max_length=120,
                    verbose_name='public name')),
                ('master', models.ForeignKey(on_delete=models.CASCADE,
                    to='campaigns.BasketCampaign',
                    editable=False,
                    related_name='translations',
                    null=True)),
            ],
            options={
                'managed': True,
                'db_table': 'campaigns_basketcampaign_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'verbose_name': 'Campaign Translation',
            }, ),
        migrations.CreateModel(
            name='BasketCondition',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            }, ),
        migrations.CreateModel(
            name='BasketDiscountEffect',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
            ],
            options={
                'abstract': False,
            }, ),
        migrations.CreateModel(
            name='BasketLineEffect',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
            ],
            options={
                'abstract': False,
            }, ),
        migrations.CreateModel(
            name='CatalogCampaign',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('name', models.CharField(
                    help_text='The name for this campaign.',
                    max_length=120,
                    verbose_name='name')),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    editable=False,
                    blank=True,
                    max_length=64,
                    null=True,
                    unique=True)),
                ('active', models.BooleanField(
                    help_text=
                    'Check this if the campaign is currently active. Please also set a start and end date.',
                    verbose_name='active',
                    default=False)),
                ('start_datetime', models.DateTimeField(
                    blank=True,
                    help_text=
                    'The date and time the campaign starts. This is only applicable if the campaign is marked as active.',
                    null=True,
                    verbose_name='start date and time')),
                ('end_datetime', models.DateTimeField(
                    blank=True,
                    help_text=
                    'The date and time the campaign ends. This is only applicable if the campaign is marked as active.',
                    null=True,
                    verbose_name='end date and time')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    auto_now=True, verbose_name='modified on')),
            ],
            options={
                'abstract': False,
                'verbose_name_plural': 'Campaigns',
                'verbose_name': 'Campaign',
            },
            bases=(shuup.utils.properties.MoneyPropped,
                   parler.models.TranslatableModelMixin, models.Model), ),
        migrations.CreateModel(
            name='CatalogCampaignLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    max_length=256, verbose_name='message')),
                ('identifier', models.CharField(
                    blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(
                    enum=shuup.utils.analog.LogEntryKind,
                    verbose_name='log entry kind',
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(on_delete=models.CASCADE,
                    to='campaigns.CatalogCampaign',
                    related_name='log_entries',
                    verbose_name='target')),
                ('user', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.PROTECT,
                    null=True,
                    verbose_name='user')),
            ],
            options={
                'abstract': False,
            }, ),
        migrations.CreateModel(
            name='CatalogCampaignTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('language_code', models.CharField(
                    max_length=15, db_index=True, verbose_name='Language')),
                ('public_name', models.CharField(
                    blank=True,
                    help_text='The campaign name to show in the store front.',
                    max_length=120)),
                ('master', models.ForeignKey(on_delete=models.CASCADE,
                    to='campaigns.CatalogCampaign',
                    editable=False,
                    related_name='translations',
                    null=True)),
            ],
            options={
                'managed': True,
                'db_table': 'campaigns_catalogcampaign_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'verbose_name': 'Campaign Translation',
            }, ),
        migrations.CreateModel(
            name='CatalogFilter',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('active', models.BooleanField(
                    verbose_name='active', default=True)),
            ],
            options={
                'abstract': False,
            }, ),
        migrations.CreateModel(
            name='CatalogFilterCachedShopProduct',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
            ], ),
        migrations.CreateModel(
            name='ContactGroupSalesRange',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('min_value', shuup.core.fields.MoneyValueField(
                    blank=True,
                    decimal_places=9,
                    null=True,
                    max_digits=36,
                    verbose_name='min amount')),
                ('max_value', shuup.core.fields.MoneyValueField(
                    blank=True,
                    decimal_places=9,
                    null=True,
                    max_digits=36,
                    verbose_name='max amount')),
                ('group', models.ForeignKey(on_delete=models.CASCADE,
                    to='shuup.ContactGroup',
                    related_name='+',
                    verbose_name='group')),
                ('shop', models.ForeignKey(on_delete=models.CASCADE,
                    to='shuup.Shop', related_name='+', verbose_name='shop')),
            ], ),
        migrations.CreateModel(
            name='ContextCondition',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            }, ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('code', models.CharField(max_length=12)),
                ('usage_limit_customer', models.PositiveIntegerField(
                    blank=True,
                    help_text=
                    'Limit the amount of usages per a single customer.',
                    null=True,
                    verbose_name='usage limit per customer')),
                ('usage_limit', models.PositiveIntegerField(
                    blank=True,
                    help_text=
                    'Set the absolute limit of usages for this coupon. If the limit is zero (0) coupon cannot be used.',
                    null=True,
                    verbose_name='usage limit')),
                ('active', models.BooleanField(
                    verbose_name='is active', default=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    auto_now=True, verbose_name='modified on')),
                ('created_by', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    verbose_name='created by',
                    related_name='+')),
                ('modified_by', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    verbose_name='modified by',
                    related_name='+')),
            ], ),
        migrations.CreateModel(
            name='CouponLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    max_length=256, verbose_name='message')),
                ('identifier', models.CharField(
                    blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(
                    enum=shuup.utils.analog.LogEntryKind,
                    verbose_name='log entry kind',
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(on_delete=models.CASCADE,
                    to='campaigns.Coupon',
                    related_name='log_entries',
                    verbose_name='target')),
                ('user', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.PROTECT,
                    null=True,
                    verbose_name='user')),
            ],
            options={
                'abstract': False,
            }, ),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    auto_now=True, verbose_name='modified on')),
                ('coupon', models.ForeignKey(on_delete=models.CASCADE,
                    to='campaigns.Coupon', related_name='usages')),
                ('created_by', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    verbose_name='created by',
                    related_name='+')),
                ('modified_by', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    verbose_name='modified by',
                    related_name='+')),
                ('order', models.ForeignKey(on_delete=models.CASCADE,
                    to='shuup.Order', related_name='coupon_usages')),
            ], ),
        migrations.CreateModel(
            name='CouponUsageLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    max_length=256, verbose_name='message')),
                ('identifier', models.CharField(
                    blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(
                    enum=shuup.utils.analog.LogEntryKind,
                    verbose_name='log entry kind',
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(on_delete=models.CASCADE,
                    to='campaigns.CouponUsage',
                    related_name='log_entries',
                    verbose_name='target')),
                ('user', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.PROTECT,
                    null=True,
                    verbose_name='user')),
            ],
            options={
                'abstract': False,
            }, ),
        migrations.CreateModel(
            name='ProductDiscountEffect',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
            ],
            options={
                'abstract': False,
            }, ),
        migrations.CreateModel(
            name='BasketDiscountAmount',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketDiscountEffect',
                    on_delete=models.CASCADE)),
                ('discount_amount', shuup.core.fields.MoneyValueField(
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    help_text='Flat amount of discount.',
                    null=True,
                    verbose_name='discount amount',
                    default=None)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect', ), ),
        migrations.CreateModel(
            name='BasketDiscountPercentage',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketDiscountEffect')),
                ('discount_percentage', models.DecimalField(
                    decimal_places=5,
                    max_digits=6,
                    blank=True,
                    help_text='The discount percentage for this campaign.',
                    null=True,
                    verbose_name='discount percentage')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect', ), ),
        migrations.CreateModel(
            name='BasketMaxTotalAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketCondition')),
                ('amount_value', shuup.core.fields.MoneyValueField(
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    null=True,
                    verbose_name='maximum basket total amount',
                    default=None)),
            ],
            options={
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped,
                   'campaigns.basketcondition'), ),
        migrations.CreateModel(
            name='BasketMaxTotalProductAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketCondition')),
                ('product_count', models.DecimalField(
                    blank=True,
                    decimal_places=9,
                    null=True,
                    max_digits=36,
                    verbose_name='maximum product count in basket')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition', ), ),
        migrations.CreateModel(
            name='BasketTotalAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketCondition')),
                ('amount_value', shuup.core.fields.MoneyValueField(
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    null=True,
                    verbose_name='basket total amount',
                    default=None)),
            ],
            options={
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped,
                   'campaigns.basketcondition'), ),
        migrations.CreateModel(
            name='BasketTotalProductAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketCondition')),
                ('product_count', models.DecimalField(
                    blank=True,
                    decimal_places=9,
                    null=True,
                    max_digits=36,
                    verbose_name='product count in basket')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition', ), ),
        migrations.CreateModel(
            name='CategoryFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.CatalogFilter')),
                ('categories', models.ManyToManyField(
                    to='shuup.Category', verbose_name='categories')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter', ), ),
        migrations.CreateModel(
            name='CategoryProductsBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketCondition')),
                ('operator', enumfields.fields.EnumIntegerField(
                    enum=shuup.campaigns.models.basket_conditions.
                    ComparisonOperator,
                    verbose_name='operator',
                    default=1)),
                ('quantity', models.PositiveIntegerField(
                    verbose_name='quantity', default=1)),
                ('categories', models.ManyToManyField(
                    to='shuup.Category',
                    verbose_name='categories',
                    related_name=
                    '_categoryproductsbasketcondition_categories_+')),
                ('excluded_categories', models.ManyToManyField(
                    blank=True,
                    help_text=
                    "If the customer has even a single product in the basket from these categories this rule won't match thus the campaign cannot be applied to the basket.",
                    to='shuup.Category',
                    verbose_name='excluded categories',
                    related_name=
                    '_categoryproductsbasketcondition_excluded_categories_+')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition', ), ),
        migrations.CreateModel(
            name='ContactBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketCondition')),
                ('contacts', models.ManyToManyField(
                    to='shuup.Contact', verbose_name='contacts')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition', ), ),
        migrations.CreateModel(
            name='ContactCondition',
            fields=[
                ('contextcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.ContextCondition')),
                ('contacts', models.ManyToManyField(
                    to='shuup.Contact', verbose_name='contacts')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.contextcondition', ), ),
        migrations.CreateModel(
            name='ContactGroupBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketCondition')),
                ('contact_groups', models.ManyToManyField(
                    to='shuup.ContactGroup', verbose_name='contact groups')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition', ), ),
        migrations.CreateModel(
            name='ContactGroupCondition',
            fields=[
                ('contextcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.ContextCondition')),
                ('contact_groups', models.ManyToManyField(
                    to='shuup.ContactGroup', verbose_name='contact groups')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.contextcondition', ), ),
        migrations.CreateModel(
            name='DiscountFromCategoryProducts',
            fields=[
                ('basketlineeffect_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketLineEffect')),
                ('discount_amount', shuup.core.fields.MoneyValueField(
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    help_text='Flat amount of discount.',
                    null=True,
                    verbose_name='discount amount',
                    default=None)),
                ('discount_percentage', models.DecimalField(
                    decimal_places=5,
                    max_digits=6,
                    blank=True,
                    help_text='The discount percentage for this campaign.',
                    null=True,
                    verbose_name='discount percentage')),
                ('category', models.ForeignKey(on_delete=models.CASCADE,
                    to='shuup.Category', verbose_name='category')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketlineeffect', ), ),
        migrations.CreateModel(
            name='DiscountFromProduct',
            fields=[
                ('basketlineeffect_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketLineEffect')),
                ('per_line_discount', models.BooleanField(
                    help_text=
                    'Uncheck this if you want to give discount for each matched product.',
                    verbose_name='per line discount',
                    default=True)),
                ('discount_amount', shuup.core.fields.MoneyValueField(
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    help_text='Flat amount of discount.',
                    null=True,
                    verbose_name='discount amount',
                    default=None)),
                ('products', models.ManyToManyField(
                    to='shuup.Product', verbose_name='product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketlineeffect', ), ),
        migrations.CreateModel(
            name='FreeProductLine',
            fields=[
                ('basketlineeffect_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketLineEffect')),
                ('quantity', shuup.core.fields.QuantityField(
                    decimal_places=9,
                    max_digits=36,
                    verbose_name='quantity',
                    default=1)),
                ('products', models.ManyToManyField(
                    to='shuup.Product', verbose_name='product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketlineeffect', ), ),
        migrations.CreateModel(
            name='HourBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketCondition')),
                ('hour_start', models.TimeField(
                    help_text='12pm is considered noon and 12am as midnight.',
                    verbose_name='start time')),
                ('hour_end', models.TimeField(
                    help_text=
                    '12pm is considered noon and 12am as midnight. End time is not considered match.',
                    verbose_name='end time')),
                ('days', models.CharField(
                    max_length=255,
                    verbose_name='days',
                    validators=[
                        django.core.validators.RegexValidator(
                            re.compile('^[\\d,]+\\Z', 32),
                            'Enter only digits separated by commas.',
                            'invalid')
                    ])),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition', ), ),
        migrations.CreateModel(
            name='HourCondition',
            fields=[
                ('contextcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.ContextCondition')),
                ('hour_start', models.TimeField(
                    help_text='12pm is considered noon and 12am as midnight.',
                    verbose_name='start time')),
                ('hour_end', models.TimeField(
                    help_text=
                    '12pm is considered noon and 12am as midnight. End time is not considered match.',
                    verbose_name='end time')),
                ('days', models.CharField(
                    max_length=255,
                    verbose_name='days',
                    validators=[
                        django.core.validators.RegexValidator(
                            re.compile('^[\\d,]+\\Z', 32),
                            'Enter only digits separated by commas.',
                            'invalid')
                    ])),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.contextcondition', ), ),
        migrations.CreateModel(
            name='ProductDiscountAmount',
            fields=[
                ('productdiscounteffect_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.ProductDiscountEffect')),
                ('discount_amount', shuup.core.fields.MoneyValueField(
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    help_text='Flat amount of discount.',
                    null=True,
                    verbose_name='discount amount',
                    default=None)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.productdiscounteffect', ), ),
        migrations.CreateModel(
            name='ProductDiscountPercentage',
            fields=[
                ('productdiscounteffect_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.ProductDiscountEffect')),
                ('discount_percentage', models.DecimalField(
                    decimal_places=5,
                    max_digits=6,
                    blank=True,
                    help_text='The discount percentage for this campaign.',
                    null=True,
                    verbose_name='discount percentage')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.productdiscounteffect', ), ),
        migrations.CreateModel(
            name='ProductFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.CatalogFilter')),
                ('products', models.ManyToManyField(
                    to='shuup.Product', verbose_name='product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter', ), ),
        migrations.CreateModel(
            name='ProductsInBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.BasketCondition')),
                ('operator', enumfields.fields.EnumIntegerField(
                    enum=shuup.campaigns.models.basket_conditions.
                    ComparisonOperator,
                    verbose_name='operator',
                    default=1)),
                ('quantity', models.PositiveIntegerField(
                    verbose_name='quantity', default=1)),
                ('products', models.ManyToManyField(
                    blank=True, to='shuup.Product', verbose_name='products')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition', ), ),
        migrations.CreateModel(
            name='ProductTypeFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(
                    on_delete=models.CASCADE,
                    auto_created=True,
                    primary_key=True,
                    parent_link=True,
                    serialize=False,
                    to='campaigns.CatalogFilter')),
                ('product_types', models.ManyToManyField(
                    to='shuup.ProductType', verbose_name='product Types')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter', ), ),
        migrations.AddField(
            model_name='productdiscounteffect',
            name='campaign',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='campaigns.CatalogCampaign',
                related_name='effects',
                verbose_name='campaign'), ),
        migrations.AddField(
            model_name='productdiscounteffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='contenttypes.ContentType',
                editable=False,
                related_name=
                'polymorphic_campaigns.productdiscounteffect_set+',
                null=True), ),
        migrations.AddField(
            model_name='contextcondition',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='contenttypes.ContentType',
                editable=False,
                related_name='polymorphic_campaigns.contextcondition_set+',
                null=True), ),
        migrations.AddField(
            model_name='catalogfiltercachedshopproduct',
            name='filter',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='campaigns.CatalogFilter',
                related_name='cached_shop_products'), ),
        migrations.AddField(
            model_name='catalogfiltercachedshopproduct',
            name='shop_product',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='shuup.ShopProduct',
                related_name='cached_catalog_campaign_filters'), ),
        migrations.AddField(
            model_name='catalogfilter',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='contenttypes.ContentType',
                editable=False,
                related_name='polymorphic_campaigns.catalogfilter_set+',
                null=True), ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='conditions',
            field=models.ManyToManyField(
                blank=True,
                to='campaigns.ContextCondition',
                related_name='campaign'), ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='created_by',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                verbose_name='created by',
                related_name='+'), ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='filters',
            field=models.ManyToManyField(
                blank=True,
                to='campaigns.CatalogFilter',
                related_name='campaign'), ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='modified_by',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                verbose_name='modified by',
                related_name='+'), ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='shop',
            field=models.ForeignKey(on_delete=models.CASCADE,
                help_text='The shop where the campaign is active.',
                to='shuup.Shop',
                verbose_name='shop'), ),
        migrations.AddField(
            model_name='basketlineeffect',
            name='campaign',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='campaigns.BasketCampaign',
                related_name='line_effects',
                verbose_name='campaign'), ),
        migrations.AddField(
            model_name='basketlineeffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='contenttypes.ContentType',
                editable=False,
                related_name='polymorphic_campaigns.basketlineeffect_set+',
                null=True), ),
        migrations.AddField(
            model_name='basketdiscounteffect',
            name='campaign',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='campaigns.BasketCampaign',
                related_name='discount_effects',
                verbose_name='campaign'), ),
        migrations.AddField(
            model_name='basketdiscounteffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='contenttypes.ContentType',
                editable=False,
                related_name='polymorphic_campaigns.basketdiscounteffect_set+',
                null=True), ),
        migrations.AddField(
            model_name='basketcondition',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE,
                to='contenttypes.ContentType',
                editable=False,
                related_name='polymorphic_campaigns.basketcondition_set+',
                null=True), ),
        migrations.AddField(
            model_name='basketcampaign',
            name='conditions',
            field=models.ManyToManyField(
                blank=True,
                to='campaigns.BasketCondition',
                related_name='campaign'), ),
        migrations.AddField(
            model_name='basketcampaign',
            name='coupon',
            field=models.OneToOneField(
                on_delete=models.CASCADE,
                blank=True,
                to='campaigns.Coupon',
                null=True,
                verbose_name='coupon',
                related_name='campaign'), ),
        migrations.AddField(
            model_name='basketcampaign',
            name='created_by',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                verbose_name='created by',
                related_name='+'), ),
        migrations.AddField(
            model_name='basketcampaign',
            name='modified_by',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                verbose_name='modified by',
                related_name='+'), ),
        migrations.AddField(
            model_name='basketcampaign',
            name='shop',
            field=models.ForeignKey(on_delete=models.CASCADE,
                help_text='The shop where the campaign is active.',
                to='shuup.Shop',
                verbose_name='shop'), ),
        migrations.AlterUniqueTogether(
            name='contactgroupsalesrange',
            unique_together=set([('group', 'shop')]), ),
        migrations.AlterUniqueTogether(
            name='catalogcampaigntranslation',
            unique_together=set([('language_code', 'master')]), ),
        migrations.AlterUniqueTogether(
            name='basketcampaigntranslation',
            unique_together=set([('language_code', 'master')]), ),
    ]
