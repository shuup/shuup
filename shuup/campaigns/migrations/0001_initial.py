# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
import parler.models
from django.conf import settings
from django.db import migrations, models

import shuup.core.fields
import shuup.utils.properties


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BasketCampaign',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=120, help_text='The name for this campaign.', verbose_name='name')),
                ('identifier', shuup.core.fields.InternalIdentifierField(max_length=64, null=True, unique=True, editable=False, blank=True)),
                ('active', models.BooleanField(verbose_name='active', default=False)),
                ('start_datetime', models.DateTimeField(blank=True, verbose_name='start date and time', null=True)),
                ('end_datetime', models.DateTimeField(blank=True, verbose_name='end date and time', null=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
                ('basket_line_text', models.CharField(max_length=120, help_text='This text will be shown in basket.', verbose_name='basket line text')),
            ],
            options={
                'verbose_name': 'Campaign',
                'verbose_name_plural': 'Campaigns',
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped, parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='BasketCampaignTranslation',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('language_code', models.CharField(db_index=True, max_length=15, verbose_name='Language')),
                ('public_name', models.CharField(verbose_name='public name', max_length=120)),
                ('master', models.ForeignKey(on_delete=models.CASCADE, related_name='translations', to='campaigns.BasketCampaign', null=True, editable=False)),
            ],
            options={
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Campaign Translation',
                'managed': True,
                'db_table': 'campaigns_basketcampaign_translation',
            },
        ),
        migrations.CreateModel(
            name='BasketCondition',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BasketDiscountEffect',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BasketLineEffect',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CatalogCampaign',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=120, help_text='The name for this campaign.', verbose_name='name')),
                ('identifier', shuup.core.fields.InternalIdentifierField(max_length=64, null=True, unique=True, editable=False, blank=True)),
                ('active', models.BooleanField(verbose_name='active', default=False)),
                ('start_datetime', models.DateTimeField(blank=True, verbose_name='start date and time', null=True)),
                ('end_datetime', models.DateTimeField(blank=True, verbose_name='end date and time', null=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
            ],
            options={
                'verbose_name': 'Campaign',
                'verbose_name_plural': 'Campaigns',
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped, parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='CatalogCampaignTranslation',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('language_code', models.CharField(db_index=True, max_length=15, verbose_name='Language')),
                ('public_name', models.CharField(max_length=120, blank=True)),
                ('master', models.ForeignKey(on_delete=models.CASCADE, related_name='translations', to='campaigns.CatalogCampaign', null=True, editable=False)),
            ],
            options={
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Campaign Translation',
                'managed': True,
                'db_table': 'campaigns_catalogcampaign_translation',
            },
        ),
        migrations.CreateModel(
            name='CatalogFilter',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('active', models.BooleanField(verbose_name='active', default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ContactGroupSalesRange',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('min_value', shuup.core.fields.MoneyValueField(blank=True, decimal_places=9, verbose_name='min amount', null=True, max_digits=36)),
                ('max_value', shuup.core.fields.MoneyValueField(blank=True, decimal_places=9, verbose_name='max amount', null=True, max_digits=36)),
                ('group', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='shuup.ContactGroup', verbose_name='group')),
                ('shop', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='shuup.Shop', verbose_name='shop')),
            ],
        ),
        migrations.CreateModel(
            name='ContextCondition',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=12)),
                ('usage_limit_customer', models.PositiveIntegerField(blank=True, help_text='Limit the amount of usages per a single customer.', verbose_name='usage limit per customer', null=True)),
                ('usage_limit', models.PositiveIntegerField(blank=True, help_text='Set the absolute limit of usages for this coupon. If the limit is zero (0) coupon cannot be used.', verbose_name='usage limit', null=True)),
                ('active', models.BooleanField(verbose_name='is active', default=False)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='created by')),
                ('modified_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='modified by')),
            ],
        ),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
                ('coupon', models.ForeignKey(on_delete=models.CASCADE, related_name='usages', to='campaigns.Coupon')),
                ('created_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='created by')),
                ('modified_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='modified by')),
                ('order', models.ForeignKey(on_delete=models.CASCADE, related_name='coupon_usages', to='shuup.Order')),
            ],
        ),
        migrations.CreateModel(
            name='ProductDiscountEffect',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BasketDiscountAmount',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketDiscountEffect', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('discount_amount', shuup.core.fields.MoneyValueField(blank=True, null=True, verbose_name='discount amount', help_text='Flat amount of discount.', decimal_places=9, default=None, max_digits=36)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect',),
        ),
        migrations.CreateModel(
            name='BasketDiscountPercentage',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketDiscountEffect', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('discount_percentage', models.DecimalField(blank=True, null=True, verbose_name='discount percentage', help_text='The discount percentage for this campaign.', decimal_places=5, max_digits=6)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect',),
        ),
        migrations.CreateModel(
            name='BasketMaxTotalAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketCondition', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('amount_value', shuup.core.fields.MoneyValueField(blank=True, null=True, verbose_name='maximum basket total amount', decimal_places=9, default=None, max_digits=36)),
            ],
            options={
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped, 'campaigns.basketcondition'),
        ),
        migrations.CreateModel(
            name='BasketMaxTotalProductAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketCondition', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('product_count', models.DecimalField(blank=True, decimal_places=9, verbose_name='maximum product count in basket', null=True, max_digits=36)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='BasketTotalAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketCondition', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('amount_value', shuup.core.fields.MoneyValueField(blank=True, null=True, verbose_name='basket total amount', decimal_places=9, default=None, max_digits=36)),
            ],
            options={
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped, 'campaigns.basketcondition'),
        ),
        migrations.CreateModel(
            name='BasketTotalProductAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketCondition', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('product_count', models.DecimalField(blank=True, decimal_places=9, verbose_name='product count in basket', null=True, max_digits=36)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='CategoryFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.CatalogFilter', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('categories', models.ManyToManyField(verbose_name='categories', to='shuup.Category')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter',),
        ),
        migrations.CreateModel(
            name='ContactBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketCondition', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('contacts', models.ManyToManyField(verbose_name='contacts', to='shuup.Contact')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='ContactCondition',
            fields=[
                ('contextcondition_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.ContextCondition', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('contacts', models.ManyToManyField(verbose_name='contacts', to='shuup.Contact')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.contextcondition',),
        ),
        migrations.CreateModel(
            name='ContactGroupBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketCondition', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('contact_groups', models.ManyToManyField(verbose_name='contact groups', to='shuup.ContactGroup')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='ContactGroupCondition',
            fields=[
                ('contextcondition_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.ContextCondition', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('contact_groups', models.ManyToManyField(verbose_name='contact groups', to='shuup.ContactGroup')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.contextcondition',),
        ),
        migrations.CreateModel(
            name='DiscountFromProduct',
            fields=[
                ('basketlineeffect_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketLineEffect', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('per_line_discount', models.BooleanField(verbose_name='per line discount', help_text='Uncheck this if you want to give discount for each matched product.', default=True)),
                ('discount_amount', shuup.core.fields.MoneyValueField(blank=True, null=True, verbose_name='discount amount', help_text='Flat amount of discount.', decimal_places=9, default=None, max_digits=36)),
                ('products', models.ManyToManyField(verbose_name='product', to='shuup.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketlineeffect',),
        ),
        migrations.CreateModel(
            name='FreeProductLine',
            fields=[
                ('basketlineeffect_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketLineEffect', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='quantity')),
                ('products', models.ManyToManyField(verbose_name='product', to='shuup.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketlineeffect',),
        ),
        migrations.CreateModel(
            name='ProductDiscountAmount',
            fields=[
                ('productdiscounteffect_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.ProductDiscountEffect', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('discount_amount', shuup.core.fields.MoneyValueField(blank=True, null=True, verbose_name='discount amount', help_text='Flat amount of discount.', decimal_places=9, default=None, max_digits=36)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.productdiscounteffect',),
        ),
        migrations.CreateModel(
            name='ProductDiscountPercentage',
            fields=[
                ('productdiscounteffect_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.ProductDiscountEffect', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('discount_percentage', models.DecimalField(blank=True, null=True, verbose_name='discount percentage', help_text='The discount percentage for this campaign.', decimal_places=5, max_digits=6)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.productdiscounteffect',),
        ),
        migrations.CreateModel(
            name='ProductFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.CatalogFilter', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('products', models.ManyToManyField(verbose_name='product', to='shuup.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter',),
        ),
        migrations.CreateModel(
            name='ProductsInBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.BasketCondition', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='quantity')),
                ('products', models.ManyToManyField(blank=True, verbose_name='products', to='shuup.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='ProductTypeFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(on_delete=models.CASCADE, to='campaigns.CatalogFilter', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('product_types', models.ManyToManyField(verbose_name='product Types', to='shuup.ProductType')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter',),
        ),
        migrations.AddField(
            model_name='productdiscounteffect',
            name='campaign',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='effects', to='campaigns.CatalogCampaign', verbose_name='campaign'),
        ),
        migrations.AddField(
            model_name='productdiscounteffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='polymorphic_campaigns.productdiscounteffect_set+', to='contenttypes.ContentType', null=True, editable=False),
        ),
        migrations.AddField(
            model_name='contextcondition',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='polymorphic_campaigns.contextcondition_set+', to='contenttypes.ContentType', null=True, editable=False),
        ),
        migrations.AddField(
            model_name='catalogfilter',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='polymorphic_campaigns.catalogfilter_set+', to='contenttypes.ContentType', null=True, editable=False),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='conditions',
            field=models.ManyToManyField(blank=True, related_name='campaign', to='campaigns.ContextCondition'),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='created_by',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='created by'),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='filters',
            field=models.ManyToManyField(blank=True, related_name='campaign', to='campaigns.CatalogFilter'),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='modified_by',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='modified by'),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='shop',
            field=models.ForeignKey(on_delete=models.CASCADE, to='shuup.Shop', verbose_name='shop', help_text='The shop where campaign is active.'),
        ),
        migrations.AddField(
            model_name='basketlineeffect',
            name='campaign',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='line_effects', to='campaigns.BasketCampaign', verbose_name='campaign'),
        ),
        migrations.AddField(
            model_name='basketlineeffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='polymorphic_campaigns.basketlineeffect_set+', to='contenttypes.ContentType', null=True, editable=False),
        ),
        migrations.AddField(
            model_name='basketdiscounteffect',
            name='campaign',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='discount_effects', to='campaigns.BasketCampaign', verbose_name='campaign'),
        ),
        migrations.AddField(
            model_name='basketdiscounteffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='polymorphic_campaigns.basketdiscounteffect_set+', to='contenttypes.ContentType', null=True, editable=False),
        ),
        migrations.AddField(
            model_name='basketcondition',
            name='polymorphic_ctype',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='polymorphic_campaigns.basketcondition_set+', to='contenttypes.ContentType', null=True, editable=False),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='conditions',
            field=models.ManyToManyField(blank=True, related_name='campaign', to='campaigns.BasketCondition'),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='coupon',
            field=models.OneToOneField(on_delete=models.CASCADE, verbose_name='coupon', blank=True, related_name='campaign', to='campaigns.Coupon', null=True),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='created_by',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='created by'),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='modified_by',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='modified by'),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='shop',
            field=models.ForeignKey(on_delete=models.CASCADE, to='shuup.Shop', verbose_name='shop', help_text='The shop where campaign is active.'),
        ),
        migrations.AlterUniqueTogether(
            name='contactgroupsalesrange',
            unique_together=set([('group', 'shop')]),
        ),
        migrations.AlterUniqueTogether(
            name='catalogcampaigntranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='basketcampaigntranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
