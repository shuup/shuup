# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import shuup.core.fields
import shuup.utils.properties
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shuup', '0027_contact_group_behavior'),
    ]

    operations = [
        migrations.CreateModel(
            name='BasketCampaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=120, help_text='The name for this campaign.')),
                ('identifier', shuup.core.fields.InternalIdentifierField(unique=True, null=True, blank=True, editable=False, max_length=64)),
                ('active', models.BooleanField(verbose_name='active', default=False)),
                ('start_datetime', models.DateTimeField(verbose_name='start date and time', null=True, blank=True)),
                ('end_datetime', models.DateTimeField(verbose_name='end date and time', null=True, blank=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
                ('basket_line_text', models.CharField(verbose_name='basket line text', max_length=120, help_text='This text will be shown in basket.')),
            ],
            options={
                'verbose_name': 'Campaign',
                'verbose_name_plural': 'Campaigns',
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped, models.Model),
        ),
        migrations.CreateModel(
            name='BasketCampaignTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('public_name', models.CharField(max_length=120)),
                ('master', models.ForeignKey(to='campaigns.BasketCampaign', null=True, related_name='translations', editable=False)),
            ],
            options={
                'verbose_name': 'Campaign Translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
                'db_table': 'campaigns_basketcampaign_translation',
            },
        ),
        migrations.CreateModel(
            name='BasketCondition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BasketDiscountEffect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BasketLineEffect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CatalogCampaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=120, help_text='The name for this campaign.')),
                ('identifier', shuup.core.fields.InternalIdentifierField(unique=True, null=True, blank=True, editable=False, max_length=64)),
                ('active', models.BooleanField(verbose_name='active', default=False)),
                ('start_datetime', models.DateTimeField(verbose_name='start date and time', null=True, blank=True)),
                ('end_datetime', models.DateTimeField(verbose_name='end date and time', null=True, blank=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
            ],
            options={
                'verbose_name': 'Campaign',
                'verbose_name_plural': 'Campaigns',
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped, models.Model),
        ),
        migrations.CreateModel(
            name='CatalogCampaignTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('public_name', models.CharField(blank=True, max_length=120)),
                ('master', models.ForeignKey(to='campaigns.CatalogCampaign', null=True, related_name='translations', editable=False)),
            ],
            options={
                'verbose_name': 'Campaign Translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
                'db_table': 'campaigns_catalogcampaign_translation',
            },
        ),
        migrations.CreateModel(
            name='CatalogFilter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('active', models.BooleanField(verbose_name='active', default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ContactGroupSalesRange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('min_value', shuup.core.fields.MoneyValueField(verbose_name='min amount', null=True, blank=True, max_digits=36, decimal_places=9)),
                ('max_value', shuup.core.fields.MoneyValueField(verbose_name='max amount', null=True, blank=True, max_digits=36, decimal_places=9)),
                ('group', models.ForeignKey(verbose_name='group', to='shuup.ContactGroup', related_name='+')),
                ('shop', models.ForeignKey(verbose_name='shop', to='shuup.Shop', related_name='+')),
            ],
        ),
        migrations.CreateModel(
            name='ContextCondition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('code', models.CharField(max_length=12)),
                ('usage_limit_customer', models.PositiveIntegerField(verbose_name='usage limit per customer', null=True, blank=True, help_text='Limit the amount of usages per a single customer.')),
                ('usage_limit', models.PositiveIntegerField(verbose_name='usage limit', null=True, blank=True, help_text='Set the absolute limit of usages for this coupon. If the limit is zero (0) coupon cannot be used.')),
                ('active', models.BooleanField(verbose_name='is active', default=False)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
                ('created_by', models.ForeignKey(verbose_name='created by', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, related_name='+')),
                ('modified_by', models.ForeignKey(verbose_name='modified by', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, related_name='+')),
            ],
        ),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
                ('coupon', models.ForeignKey(to='campaigns.Coupon', related_name='usages')),
                ('created_by', models.ForeignKey(verbose_name='created by', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, related_name='+')),
                ('modified_by', models.ForeignKey(verbose_name='modified by', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, related_name='+')),
                ('order', models.ForeignKey(to='shuup.Order', related_name='coupon_usages')),
            ],
        ),
        migrations.CreateModel(
            name='ProductDiscountEffect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BasketDiscountAmount',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(to='campaigns.BasketDiscountEffect', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('discount_amount', shuup.core.fields.MoneyValueField(verbose_name='discount amount', decimal_places=9, max_digits=36, default=None, null=True, blank=True, help_text='Flat amount of discount.')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect',),
        ),
        migrations.CreateModel(
            name='BasketDiscountPercentage',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(to='campaigns.BasketDiscountEffect', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('discount_percentage', models.DecimalField(verbose_name='discount percentage', decimal_places=5, max_digits=6, null=True, blank=True, help_text='The discount percentage for this campaign.')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect',),
        ),
        migrations.CreateModel(
            name='BasketMaxTotalAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(to='campaigns.BasketCondition', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('amount_value', shuup.core.fields.MoneyValueField(verbose_name='maximum basket total amount', decimal_places=9, max_digits=36, default=None, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped, 'campaigns.basketcondition'),
        ),
        migrations.CreateModel(
            name='BasketMaxTotalProductAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(to='campaigns.BasketCondition', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('product_count', models.DecimalField(verbose_name='maximum product count in basket', null=True, blank=True, max_digits=36, decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='BasketTotalAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(to='campaigns.BasketCondition', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('amount_value', shuup.core.fields.MoneyValueField(verbose_name='basket total amount', decimal_places=9, max_digits=36, default=None, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(shuup.utils.properties.MoneyPropped, 'campaigns.basketcondition'),
        ),
        migrations.CreateModel(
            name='BasketTotalProductAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(to='campaigns.BasketCondition', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('product_count', models.DecimalField(verbose_name='product count in basket', null=True, blank=True, max_digits=36, decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='CategoryFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(to='campaigns.CatalogFilter', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
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
                ('basketcondition_ptr', models.OneToOneField(to='campaigns.BasketCondition', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
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
                ('contextcondition_ptr', models.OneToOneField(to='campaigns.ContextCondition', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
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
                ('basketcondition_ptr', models.OneToOneField(to='campaigns.BasketCondition', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
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
                ('contextcondition_ptr', models.OneToOneField(to='campaigns.ContextCondition', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
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
                ('basketlineeffect_ptr', models.OneToOneField(to='campaigns.BasketLineEffect', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('per_line_discount', models.BooleanField(verbose_name='per line discount', default=True, help_text='Uncheck this if you want to give discount for each matched product.')),
                ('discount_amount', shuup.core.fields.MoneyValueField(verbose_name='discount amount', decimal_places=9, max_digits=36, default=None, null=True, blank=True, help_text='Flat amount of discount.')),
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
                ('basketlineeffect_ptr', models.OneToOneField(to='campaigns.BasketLineEffect', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('quantity', models.PositiveIntegerField(verbose_name='quantity', default=1)),
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
                ('productdiscounteffect_ptr', models.OneToOneField(to='campaigns.ProductDiscountEffect', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('discount_amount', shuup.core.fields.MoneyValueField(verbose_name='discount amount', decimal_places=9, max_digits=36, default=None, null=True, blank=True, help_text='Flat amount of discount.')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.productdiscounteffect',),
        ),
        migrations.CreateModel(
            name='ProductDiscountPercentage',
            fields=[
                ('productdiscounteffect_ptr', models.OneToOneField(to='campaigns.ProductDiscountEffect', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('discount_percentage', models.DecimalField(verbose_name='discount percentage', decimal_places=5, max_digits=6, null=True, blank=True, help_text='The discount percentage for this campaign.')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.productdiscounteffect',),
        ),
        migrations.CreateModel(
            name='ProductFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(to='campaigns.CatalogFilter', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
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
                ('basketcondition_ptr', models.OneToOneField(to='campaigns.BasketCondition', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
                ('quantity', models.PositiveIntegerField(verbose_name='quantity', default=1)),
                ('products', models.ManyToManyField(verbose_name='products', blank=True, to='shuup.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='ProductTypeFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(to='campaigns.CatalogFilter', serialize=False, auto_created=True, primary_key=True, parent_link=True)),
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
            field=models.ForeignKey(verbose_name='campaign', to='campaigns.CatalogCampaign', related_name='effects'),
        ),
        migrations.AddField(
            model_name='productdiscounteffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, related_name='polymorphic_campaigns.productdiscounteffect_set+', editable=False),
        ),
        migrations.AddField(
            model_name='contextcondition',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, related_name='polymorphic_campaigns.contextcondition_set+', editable=False),
        ),
        migrations.AddField(
            model_name='catalogfilter',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, related_name='polymorphic_campaigns.catalogfilter_set+', editable=False),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='conditions',
            field=models.ManyToManyField(blank=True, related_name='campaign', to='campaigns.ContextCondition'),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='created_by',
            field=models.ForeignKey(verbose_name='created by', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, related_name='+'),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='filters',
            field=models.ManyToManyField(blank=True, related_name='campaign', to='campaigns.CatalogFilter'),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='modified_by',
            field=models.ForeignKey(verbose_name='modified by', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, related_name='+'),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='shop',
            field=models.ForeignKey(verbose_name='shop', to='shuup.Shop', help_text='The shop where campaign is active.'),
        ),
        migrations.AddField(
            model_name='basketlineeffect',
            name='campaign',
            field=models.ForeignKey(verbose_name='campaign', to='campaigns.BasketCampaign', related_name='line_effects'),
        ),
        migrations.AddField(
            model_name='basketlineeffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, related_name='polymorphic_campaigns.basketlineeffect_set+', editable=False),
        ),
        migrations.AddField(
            model_name='basketdiscounteffect',
            name='campaign',
            field=models.ForeignKey(verbose_name='campaign', to='campaigns.BasketCampaign', related_name='discount_effects'),
        ),
        migrations.AddField(
            model_name='basketdiscounteffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, related_name='polymorphic_campaigns.basketdiscounteffect_set+', editable=False),
        ),
        migrations.AddField(
            model_name='basketcondition',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, related_name='polymorphic_campaigns.basketcondition_set+', editable=False),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='conditions',
            field=models.ManyToManyField(blank=True, related_name='campaign', to='campaigns.BasketCondition'),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='coupon',
            field=models.OneToOneField(to='campaigns.Coupon', related_name='campaign', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='created_by',
            field=models.ForeignKey(verbose_name='created by', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, related_name='+'),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='modified_by',
            field=models.ForeignKey(verbose_name='modified by', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, related_name='+'),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='shop',
            field=models.ForeignKey(verbose_name='shop', to='shuup.Shop', help_text='The shop where campaign is active.'),
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
