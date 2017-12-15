# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

import django.core.validators
import django.db.models.deletion
import enumfields.fields
import jsonfield.fields
import parler.models
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
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('name', models.CharField(
                    verbose_name='name',
                    help_text='The name for this campaign.',
                    max_length=120)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    editable=False,
                    null=True,
                    blank=True,
                    max_length=64,
                    unique=True)),
                ('active', models.BooleanField(
                    default=False, verbose_name='active')),
                ('start_datetime', models.DateTimeField(
                    verbose_name='start date and time', null=True,
                    blank=True)),
                ('end_datetime', models.DateTimeField(
                    verbose_name='end date and time', null=True, blank=True)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    verbose_name='modified on', auto_now=True)),
                ('basket_line_text', models.CharField(
                    verbose_name='basket line text',
                    help_text='This text will be shown in basket.',
                    max_length=120)),
            ],
            options={
                'verbose_name': 'Campaign',
                'verbose_name_plural': 'Campaigns',
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped,
                   parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='BasketCampaignTranslation',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('public_name', models.CharField(
                    verbose_name='public name', max_length=120)),
                ('master', models.ForeignKey(
                    related_name='translations',
                    editable=False,
                    null=True,
                    to='campaigns.BasketCampaign')),
            ],
            options={
                'db_tablespace': '',
                'db_table': 'campaigns_basketcampaign_translation',
                'verbose_name': 'Campaign Translation',
                'managed': True,
                'default_permissions': (),
            },),
        migrations.CreateModel(
            name='BasketCondition',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='BasketDiscountEffect',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='BasketLineEffect',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='CatalogCampaign',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('name', models.CharField(
                    verbose_name='name',
                    help_text='The name for this campaign.',
                    max_length=120)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    editable=False,
                    null=True,
                    blank=True,
                    max_length=64,
                    unique=True)),
                ('active', models.BooleanField(
                    default=False, verbose_name='active')),
                ('start_datetime', models.DateTimeField(
                    verbose_name='start date and time', null=True,
                    blank=True)),
                ('end_datetime', models.DateTimeField(
                    verbose_name='end date and time', null=True, blank=True)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    verbose_name='modified on', auto_now=True)),
            ],
            options={
                'verbose_name': 'Campaign',
                'verbose_name_plural': 'Campaigns',
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped,
                   parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='CatalogCampaignTranslation',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('public_name', models.CharField(blank=True, max_length=120)),
                ('master', models.ForeignKey(
                    related_name='translations',
                    editable=False,
                    null=True,
                    to='campaigns.CatalogCampaign')),
            ],
            options={
                'db_tablespace': '',
                'db_table': 'campaigns_catalogcampaign_translation',
                'verbose_name': 'Campaign Translation',
                'managed': True,
                'default_permissions': (),
            },),
        migrations.CreateModel(
            name='CatalogFilter',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('active', models.BooleanField(
                    default=True, verbose_name='active')),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ContactGroupSalesRange',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('min_value', shuup.core.fields.MoneyValueField(
                    max_digits=36,
                    verbose_name='min amount',
                    null=True,
                    blank=True,
                    decimal_places=9)),
                ('max_value', shuup.core.fields.MoneyValueField(
                    max_digits=36,
                    verbose_name='max amount',
                    null=True,
                    blank=True,
                    decimal_places=9)),
                ('group', models.ForeignKey(
                    related_name='+',
                    verbose_name='group',
                    to='shuup.ContactGroup')),
                ('shop', models.ForeignKey(
                    related_name='+', verbose_name='shop', to='shuup.Shop')),
            ],),
        migrations.CreateModel(
            name='ContextCondition',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('code', models.CharField(max_length=12)),
                ('usage_limit_customer', models.PositiveIntegerField(
                    verbose_name='usage limit per customer',
                    null=True,
                    blank=True,
                    help_text=(
                        'Limit the amount of usages per a single customer.'))),
                ('usage_limit', models.PositiveIntegerField(
                    verbose_name='usage limit',
                    null=True,
                    blank=True,
                    help_text=(
                        'Set the absolute limit of usages for this coupon. '
                        'If the limit is zero (0) coupon cannot be used.')
                )),
                ('active', models.BooleanField(
                    default=False, verbose_name='is active')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    verbose_name='modified on', auto_now=True)),
                ('created_by', models.ForeignKey(
                    related_name='+',
                    on_delete=django.db.models.deletion.SET_NULL,
                    verbose_name='created by',
                    null=True,
                    blank=True,
                    to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(
                    related_name='+',
                    on_delete=django.db.models.deletion.SET_NULL,
                    verbose_name='modified by',
                    null=True,
                    blank=True,
                    to=settings.AUTH_USER_MODEL)),
            ],),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    verbose_name='modified on', auto_now=True)),
                ('coupon', models.ForeignKey(
                    related_name='usages', to='campaigns.Coupon')),
                ('created_by', models.ForeignKey(
                    related_name='+',
                    on_delete=django.db.models.deletion.SET_NULL,
                    verbose_name='created by',
                    null=True,
                    blank=True,
                    to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(
                    related_name='+',
                    on_delete=django.db.models.deletion.SET_NULL,
                    verbose_name='modified by',
                    null=True,
                    blank=True,
                    to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(
                    related_name='coupon_usages', to='shuup.Order')),
            ],),
        migrations.CreateModel(
            name='ProductDiscountEffect',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='BasketDiscountAmount',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketDiscountEffect',
                    parent_link=True,
                    primary_key=True)),
                ('discount_amount', shuup.core.fields.MoneyValueField(
                    verbose_name='discount amount',
                    null=True,
                    blank=True,
                    max_digits=36,
                    default=None,
                    help_text='Flat amount of discount.',
                    decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect',),),
        migrations.CreateModel(
            name='BasketDiscountPercentage',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketDiscountEffect',
                    parent_link=True,
                    primary_key=True)),
                ('discount_percentage', models.DecimalField(
                    verbose_name='discount percentage',
                    null=True,
                    blank=True,
                    max_digits=6,
                    help_text='The discount percentage for this campaign.',
                    decimal_places=5)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect',),),
        migrations.CreateModel(
            name='BasketMaxTotalAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketCondition',
                    parent_link=True,
                    primary_key=True)),
                ('amount_value', shuup.core.fields.MoneyValueField(
                    verbose_name='maximum basket total amount',
                    null=True,
                    blank=True,
                    max_digits=36,
                    default=None,
                    decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped,
                   'campaigns.basketcondition'),),
        migrations.CreateModel(
            name='BasketMaxTotalProductAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketCondition',
                    parent_link=True,
                    primary_key=True)),
                ('product_count', models.DecimalField(
                    max_digits=36,
                    verbose_name='maximum product count in basket',
                    null=True,
                    blank=True,
                    decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),),
        migrations.CreateModel(
            name='BasketTotalAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketCondition',
                    parent_link=True,
                    primary_key=True)),
                ('amount_value', shuup.core.fields.MoneyValueField(
                    verbose_name='basket total amount',
                    null=True,
                    blank=True,
                    max_digits=36,
                    default=None,
                    decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped,
                   'campaigns.basketcondition'),),
        migrations.CreateModel(
            name='BasketTotalProductAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketCondition',
                    parent_link=True,
                    primary_key=True)),
                ('product_count', models.DecimalField(
                    max_digits=36,
                    verbose_name='product count in basket',
                    null=True,
                    blank=True,
                    decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),),
        migrations.CreateModel(
            name='CategoryFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.CatalogFilter',
                    parent_link=True,
                    primary_key=True)),
                ('categories', models.ManyToManyField(
                    verbose_name='categories', to='shuup.Category')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter',),),
        migrations.CreateModel(
            name='ContactBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketCondition',
                    parent_link=True,
                    primary_key=True)),
                ('contacts', models.ManyToManyField(
                    verbose_name='contacts', to='shuup.Contact')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),),
        migrations.CreateModel(
            name='ContactCondition',
            fields=[
                ('contextcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.ContextCondition',
                    parent_link=True,
                    primary_key=True)),
                ('contacts', models.ManyToManyField(
                    verbose_name='contacts', to='shuup.Contact')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.contextcondition',),),
        migrations.CreateModel(
            name='ContactGroupBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketCondition',
                    parent_link=True,
                    primary_key=True)),
                ('contact_groups', models.ManyToManyField(
                    verbose_name='contact groups', to='shuup.ContactGroup')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),),
        migrations.CreateModel(
            name='ContactGroupCondition',
            fields=[
                ('contextcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.ContextCondition',
                    parent_link=True,
                    primary_key=True)),
                ('contact_groups', models.ManyToManyField(
                    verbose_name='contact groups', to='shuup.ContactGroup')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.contextcondition',),),
        migrations.CreateModel(
            name='DiscountFromProduct',
            fields=[
                ('basketlineeffect_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketLineEffect',
                    parent_link=True,
                    primary_key=True)),
                ('per_line_discount', models.BooleanField(
                    default=True,
                    verbose_name='per line discount',
                    help_text=(
                        'Uncheck this if you want to give discount for each '
                        'matched product.')
                )),
                ('discount_amount', shuup.core.fields.MoneyValueField(
                    verbose_name='discount amount',
                    null=True,
                    blank=True,
                    max_digits=36,
                    default=None,
                    help_text='Flat amount of discount.',
                    decimal_places=9)),
                ('products', models.ManyToManyField(
                    verbose_name='product', to='shuup.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketlineeffect',),),
        migrations.CreateModel(
            name='FreeProductLine',
            fields=[
                ('basketlineeffect_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketLineEffect',
                    parent_link=True,
                    primary_key=True)),
                ('quantity', models.PositiveIntegerField(
                    default=1, verbose_name='quantity')),
                ('products', models.ManyToManyField(
                    verbose_name='product', to='shuup.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketlineeffect',),),
        migrations.CreateModel(
            name='ProductDiscountAmount',
            fields=[
                ('productdiscounteffect_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.ProductDiscountEffect',
                    parent_link=True,
                    primary_key=True)),
                ('discount_amount', shuup.core.fields.MoneyValueField(
                    verbose_name='discount amount',
                    null=True,
                    blank=True,
                    max_digits=36,
                    default=None,
                    help_text='Flat amount of discount.',
                    decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.productdiscounteffect',),),
        migrations.CreateModel(
            name='ProductDiscountPercentage',
            fields=[
                ('productdiscounteffect_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.ProductDiscountEffect',
                    parent_link=True,
                    primary_key=True)),
                ('discount_percentage', models.DecimalField(
                    verbose_name='discount percentage',
                    null=True,
                    blank=True,
                    max_digits=6,
                    help_text='The discount percentage for this campaign.',
                    decimal_places=5)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.productdiscounteffect',),),
        migrations.CreateModel(
            name='ProductFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.CatalogFilter',
                    parent_link=True,
                    primary_key=True)),
                ('products', models.ManyToManyField(
                    verbose_name='product', to='shuup.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter',),),
        migrations.CreateModel(
            name='ProductsInBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketCondition',
                    parent_link=True,
                    primary_key=True)),
                ('quantity', models.PositiveIntegerField(
                    default=1, verbose_name='quantity')),
                ('products', models.ManyToManyField(
                    verbose_name='products', to='shuup.Product', blank=True)),
                ('operator', enumfields.fields.EnumIntegerField(
                    default=1,
                    verbose_name='operator',
                    enum=shuup.campaigns.models.basket_conditions.
                    ComparisonOperator)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),),
        migrations.CreateModel(
            name='ProductTypeFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.CatalogFilter',
                    parent_link=True,
                    primary_key=True)),
                ('product_types', models.ManyToManyField(
                    verbose_name='product Types', to='shuup.ProductType')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter',),),
        migrations.AddField(
            model_name='productdiscounteffect',
            name='campaign',
            field=models.ForeignKey(
                related_name='effects',
                verbose_name='campaign',
                to='campaigns.CatalogCampaign'),),
        migrations.AddField(
            model_name='productdiscounteffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(
                related_name=(
                    'polymorphic_campaigns.productdiscounteffect_set+'),
                editable=False,
                null=True,
                to='contenttypes.ContentType'),),
        migrations.AddField(
            model_name='contextcondition',
            name='polymorphic_ctype',
            field=models.ForeignKey(
                related_name='polymorphic_campaigns.contextcondition_set+',
                editable=False,
                null=True,
                to='contenttypes.ContentType'),),
        migrations.AddField(
            model_name='catalogfilter',
            name='polymorphic_ctype',
            field=models.ForeignKey(
                related_name='polymorphic_campaigns.catalogfilter_set+',
                editable=False,
                null=True,
                to='contenttypes.ContentType'),),
        migrations.AddField(
            model_name='catalogcampaign',
            name='conditions',
            field=models.ManyToManyField(
                related_name='campaign',
                to='campaigns.ContextCondition',
                blank=True),),
        migrations.AddField(
            model_name='catalogcampaign',
            name='created_by',
            field=models.ForeignKey(
                related_name='+',
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name='created by',
                null=True,
                blank=True,
                to=settings.AUTH_USER_MODEL),),
        migrations.AddField(
            model_name='catalogcampaign',
            name='filters',
            field=models.ManyToManyField(
                related_name='campaign',
                to='campaigns.CatalogFilter',
                blank=True),),
        migrations.AddField(
            model_name='catalogcampaign',
            name='modified_by',
            field=models.ForeignKey(
                related_name='+',
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name='modified by',
                null=True,
                blank=True,
                to=settings.AUTH_USER_MODEL),),
        migrations.AddField(
            model_name='catalogcampaign',
            name='shop',
            field=models.ForeignKey(
                verbose_name='shop',
                to='shuup.Shop',
                help_text='The shop where campaign is active.'),),
        migrations.AddField(
            model_name='basketlineeffect',
            name='campaign',
            field=models.ForeignKey(
                related_name='line_effects',
                verbose_name='campaign',
                to='campaigns.BasketCampaign'),),
        migrations.AddField(
            model_name='basketlineeffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(
                related_name='polymorphic_campaigns.basketlineeffect_set+',
                editable=False,
                null=True,
                to='contenttypes.ContentType'),),
        migrations.AddField(
            model_name='basketdiscounteffect',
            name='campaign',
            field=models.ForeignKey(
                related_name='discount_effects',
                verbose_name='campaign',
                to='campaigns.BasketCampaign'),),
        migrations.AddField(
            model_name='basketdiscounteffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(
                related_name='polymorphic_campaigns.basketdiscounteffect_set+',
                editable=False,
                null=True,
                to='contenttypes.ContentType'),),
        migrations.AddField(
            model_name='basketcondition',
            name='polymorphic_ctype',
            field=models.ForeignKey(
                related_name='polymorphic_campaigns.basketcondition_set+',
                editable=False,
                null=True,
                to='contenttypes.ContentType'),),
        migrations.AddField(
            model_name='basketcampaign',
            name='conditions',
            field=models.ManyToManyField(
                related_name='campaign',
                to='campaigns.BasketCondition',
                blank=True),),
        migrations.AddField(
            model_name='basketcampaign',
            name='coupon',
            field=models.OneToOneField(
                related_name='campaign',
                verbose_name='coupon',
                null=True,
                blank=True,
                to='campaigns.Coupon'),),
        migrations.AddField(
            model_name='basketcampaign',
            name='created_by',
            field=models.ForeignKey(
                related_name='+',
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name='created by',
                null=True,
                blank=True,
                to=settings.AUTH_USER_MODEL),),
        migrations.AddField(
            model_name='basketcampaign',
            name='modified_by',
            field=models.ForeignKey(
                related_name='+',
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name='modified by',
                null=True,
                blank=True,
                to=settings.AUTH_USER_MODEL),),
        migrations.AddField(
            model_name='basketcampaign',
            name='shop',
            field=models.ForeignKey(
                verbose_name='shop',
                to='shuup.Shop',
                help_text='The shop where campaign is active.'),),
        migrations.AlterUniqueTogether(
            name='contactgroupsalesrange',
            unique_together=set([('group', 'shop')]),),
        migrations.AlterUniqueTogether(
            name='catalogcampaigntranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='basketcampaigntranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.CreateModel(
            name='CategoryProductsBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketCondition',
                    parent_link=True,
                    primary_key=True)),
                ('operator', enumfields.fields.EnumIntegerField(
                    default=1,
                    verbose_name='operator',
                    enum=shuup.campaigns.models.basket_conditions.
                    ComparisonOperator)),
                ('quantity', models.PositiveIntegerField(
                    default=1, verbose_name='quantity')),
                ('category', models.ForeignKey(
                    verbose_name='category',
                    null=True,
                    blank=True,
                    to='shuup.Category')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),),
        migrations.CreateModel(
            name='DiscountFromCategoryProducts',
            fields=[
                ('basketlineeffect_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketLineEffect',
                    parent_link=True,
                    primary_key=True)),
                ('discount_amount', shuup.core.fields.MoneyValueField(
                    verbose_name='discount amount',
                    null=True,
                    blank=True,
                    max_digits=36,
                    default=None,
                    help_text='Flat amount of discount.',
                    decimal_places=9)),
                ('discount_percentage', models.DecimalField(
                    verbose_name='discount percentage',
                    null=True,
                    blank=True,
                    max_digits=6,
                    help_text='The discount percentage for this campaign.',
                    decimal_places=5)),
                ('category', models.ForeignKey(
                    verbose_name='category', to='shuup.Category')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketlineeffect',),),
        migrations.CreateModel(
            name='BasketCampaignLogEntry',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(
                    default=0,
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    related_name='log_entries',
                    verbose_name='target',
                    to='campaigns.BasketCampaign')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    verbose_name='user',
                    null=True,
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='CatalogCampaignLogEntry',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(
                    default=0,
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    related_name='log_entries',
                    verbose_name='target',
                    to='campaigns.CatalogCampaign')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    verbose_name='user',
                    null=True,
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='CouponLogEntry',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(
                    default=0,
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    related_name='log_entries',
                    verbose_name='target',
                    to='campaigns.Coupon')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    verbose_name='user',
                    null=True,
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='CouponUsageLogEntry',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(
                    default=0,
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    related_name='log_entries',
                    verbose_name='target',
                    to='campaigns.CouponUsage')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    verbose_name='user',
                    null=True,
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='CatalogFilterCachedShopProduct',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID')),
                ('filter', models.ForeignKey(
                    related_name='cached_shop_products',
                    to='campaigns.CatalogFilter')),
                ('shop_product', models.ForeignKey(
                    related_name='cached_catalog_campaign_filters',
                    to='shuup.ShopProduct')),
            ],),
        migrations.AddField(
            model_name='categoryproductsbasketcondition',
            name='categories',
            field=models.ManyToManyField(to='shuup.Category'),),
        migrations.RemoveField(
            model_name='categoryproductsbasketcondition',
            name='category',),
        migrations.AddField(
            model_name='categoryproductsbasketcondition',
            name='excluded_categories',
            field=models.ManyToManyField(
                related_name=(
                    '_categoryproductsbasketcondition_excluded_categories_+'),
                verbose_name='excluded categories',
                to='shuup.Category',
                help_text=(
                    "If the customer has even a single product in the basket "
                    "from these categories this rule won't match thus the "
                    "campaign cannot be applied to the basket."),
                blank=True),),
        migrations.AlterField(
            model_name='categoryproductsbasketcondition',
            name='categories',
            field=models.ManyToManyField(
                related_name='_categoryproductsbasketcondition_categories_+',
                to='shuup.Category'),),
        migrations.AlterField(
            model_name='freeproductline',
            name='quantity',
            field=shuup.core.fields.QuantityField(
                max_digits=36,
                default=1,
                verbose_name='quantity',
                decimal_places=9),),
        migrations.CreateModel(
            name='HourCondition',
            fields=[
                ('contextcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.ContextCondition',
                    parent_link=True,
                    primary_key=True)),
                ('hour_start', models.TimeField(verbose_name='hour start')),
                ('hour_end', models.TimeField(verbose_name='hour start')),
                ('days', models.CharField(
                    validators=[
                        django.core.validators.RegexValidator(
                            re.compile('^[\\d,]+\\Z', 32),
                            code='invalid',
                            message='Enter only digits separated by commas.')
                    ],
                    verbose_name='days',
                    max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.contextcondition',),),
        migrations.CreateModel(
            name='HourBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(
                    serialize=False,
                    auto_created=True,
                    to='campaigns.BasketCondition',
                    parent_link=True,
                    primary_key=True)),
                ('hour_start', models.TimeField(verbose_name='hour start')),
                ('hour_end', models.TimeField(verbose_name='hour start')),
                ('days', models.CharField(
                    validators=[
                        django.core.validators.RegexValidator(
                            re.compile('^[\\d,]+\\Z', 32),
                            code='invalid',
                            message='Enter only digits separated by commas.')
                    ],
                    verbose_name='days',
                    max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',)),
        migrations.AlterField(
            model_name='basketcampaign',
            name='active',
            field=models.BooleanField(
                default=False,
                verbose_name='active',
                help_text=(
                    'Check this if the campaign is currently active. '
                    'Please also set a start and end date.')
            )),
        migrations.AlterField(
            model_name='basketcampaign',
            name='end_datetime',
            field=models.DateTimeField(
                verbose_name='end date and time',
                null=True,
                blank=True,
                help_text=(
                    'The date and time the campaign ends. This is only '
                    'applicable if the campaign is marked as active.')
            )),
        migrations.AlterField(
            model_name='basketcampaign',
            name='shop',
            field=models.ForeignKey(
                verbose_name='shop',
                to='shuup.Shop',
                help_text='The shop where the campaign is active.')),
        migrations.AlterField(
            model_name='basketcampaign',
            name='start_datetime',
            field=models.DateTimeField(
                verbose_name='start date and time',
                null=True,
                blank=True,
                help_text=(
                    'The date and time the campaign starts. '
                    'This is only applicable if the campaign '
                    'is marked as active.')
            )),
        migrations.AlterField(
            model_name='basketcampaigntranslation',
            name='public_name',
            field=models.CharField(
                verbose_name='public name',
                help_text='The campaign name to show in the store front.',
                max_length=120)),
        migrations.AlterField(
            model_name='catalogcampaign',
            name='active',
            field=models.BooleanField(
                default=False,
                verbose_name='active',
                help_text=(
                    'Check this if the campaign is currently active. '
                    'Please also set a start and end date.')
            )),
        migrations.AlterField(
            model_name='catalogcampaign',
            name='end_datetime',
            field=models.DateTimeField(
                verbose_name='end date and time',
                null=True,
                blank=True,
                help_text=(
                    'The date and time the campaign ends. This is only '
                    'applicable if the campaign is marked as active.')
            )),
        migrations.AlterField(
            model_name='catalogcampaign',
            name='shop',
            field=models.ForeignKey(
                verbose_name='shop',
                to='shuup.Shop',
                help_text='The shop where the campaign is active.')),
        migrations.AlterField(
            model_name='catalogcampaign',
            name='start_datetime',
            field=models.DateTimeField(
                verbose_name='start date and time',
                null=True,
                blank=True,
                help_text=(
                    'The date and time the campaign starts. This is only '
                    'applicable if the campaign is marked as active.')
            )),
        migrations.AlterField(
            model_name='catalogcampaigntranslation',
            name='public_name',
            field=models.CharField(
                help_text='The campaign name to show in the store front.',
                blank=True,
                max_length=120)),
        migrations.AlterField(
            model_name='categoryproductsbasketcondition',
            name='categories',
            field=models.ManyToManyField(
                related_name='_categoryproductsbasketcondition_categories_+',
                verbose_name='categories',
                to='shuup.Category')),
    ]
