# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields
import django.db.models.deletion
import shoop.utils.properties
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shoop', '0015_product_minimum_price'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='BasketCampaign',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(help_text='The name for this campaign.', verbose_name='name', max_length=120)),
                ('identifier', shoop.core.fields.InternalIdentifierField(null=True, editable=False, unique=True, max_length=64, blank=True)),
                ('discount_percentage', models.DecimalField(help_text='The discount percentage for this campaign.', null=True, max_digits=6, decimal_places=5, verbose_name='discount percentage', blank=True)),
                ('discount_amount_value', shoop.core.fields.MoneyValueField(help_text='Flat amount of discount. Mutually exclusive with percentage.', null=True, max_digits=36, decimal_places=9, verbose_name='discount amount value', blank=True, default=None)),
                ('active', models.BooleanField(verbose_name='active', default=False)),
                ('start_datetime', models.DateTimeField(null=True, blank=True, verbose_name='start date and time')),
                ('end_datetime', models.DateTimeField(null=True, blank=True, verbose_name='end date and time')),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
                ('basket_line_text', models.CharField(help_text='This text will be shown in basket.', verbose_name='basket line text', max_length=120)),
            ],
            options={
                'verbose_name_plural': 'Campaigns',
                'verbose_name': 'Campaign',
                'abstract': False,
            },
            bases=(shoop.utils.properties.MoneyPropped, models.Model),
        ),
        migrations.CreateModel(
            name='BasketCampaignTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('public_name', models.CharField(max_length=120)),
                ('master', models.ForeignKey(related_name='translations', null=True, editable=False, to='campaigns.BasketCampaign')),
            ],
            options={
                'managed': True,
                'db_table': 'campaigns_basketcampaign_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Campaign Translation',
            },
        ),
        migrations.CreateModel(
            name='BasketCondition',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CatalogCampaign',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(help_text='The name for this campaign.', verbose_name='name', max_length=120)),
                ('identifier', shoop.core.fields.InternalIdentifierField(null=True, editable=False, unique=True, max_length=64, blank=True)),
                ('discount_percentage', models.DecimalField(help_text='The discount percentage for this campaign.', null=True, max_digits=6, decimal_places=5, verbose_name='discount percentage', blank=True)),
                ('discount_amount_value', shoop.core.fields.MoneyValueField(help_text='Flat amount of discount. Mutually exclusive with percentage.', null=True, max_digits=36, decimal_places=9, verbose_name='discount amount value', blank=True, default=None)),
                ('active', models.BooleanField(verbose_name='active', default=False)),
                ('start_datetime', models.DateTimeField(null=True, blank=True, verbose_name='start date and time')),
                ('end_datetime', models.DateTimeField(null=True, blank=True, verbose_name='end date and time')),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Campaigns',
                'verbose_name': 'Campaign',
                'abstract': False,
            },
            bases=(shoop.utils.properties.MoneyPropped, models.Model),
        ),
        migrations.CreateModel(
            name='CatalogCampaignTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('public_name', models.CharField(max_length=120, blank=True)),
                ('master', models.ForeignKey(related_name='translations', null=True, editable=False, to='campaigns.CatalogCampaign')),
            ],
            options={
                'managed': True,
                'db_table': 'campaigns_catalogcampaign_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Campaign Translation',
            },
        ),
        migrations.CreateModel(
            name='CatalogFilter',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('active', models.BooleanField(verbose_name='active', default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ContextCondition',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(max_length=12)),
                ('usage_limit_customer', models.PositiveIntegerField(help_text='Limit the amount of usages per a single customer.', null=True, blank=True, verbose_name='usage limit per customer')),
                ('usage_limit', models.PositiveIntegerField(help_text='Set the absolute limit of usages for this coupon. If the limit is zero (0) coupon cannot be used.', null=True, blank=True, verbose_name='usage limit')),
                ('active', models.BooleanField(verbose_name='is active', default=False)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
                ('created_by', models.ForeignKey(related_name='+', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, verbose_name='created by', blank=True)),
                ('modified_by', models.ForeignKey(related_name='+', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, verbose_name='modified by', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
                ('coupon', models.ForeignKey(related_name='usages', to='campaigns.Coupon')),
                ('created_by', models.ForeignKey(related_name='+', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, verbose_name='created by', blank=True)),
                ('modified_by', models.ForeignKey(related_name='+', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, verbose_name='modified by', blank=True)),
                ('order', models.ForeignKey(related_name='coupon_usages', to='shoop.Order')),
            ],
        ),
        migrations.CreateModel(
            name='BasketTotalAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(primary_key=True, to='campaigns.BasketCondition', parent_link=True, serialize=False, auto_created=True)),
                ('amount_value', shoop.core.fields.MoneyValueField(null=True, max_digits=36, decimal_places=9, verbose_name='basket total amount', blank=True, default=None)),
            ],
            options={
                'abstract': False,
            },
            bases=(shoop.utils.properties.MoneyPropped, 'campaigns.basketcondition'),
        ),
        migrations.CreateModel(
            name='BasketTotalProductAmountCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(primary_key=True, to='campaigns.BasketCondition', parent_link=True, serialize=False, auto_created=True)),
                ('product_count', models.DecimalField(null=True, blank=True, max_digits=6, verbose_name='product count in basket', decimal_places=5)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='CategoryFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(primary_key=True, to='campaigns.CatalogFilter', parent_link=True, serialize=False, auto_created=True)),
                ('categories', models.ManyToManyField(verbose_name='categories', to='shoop.Category')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter',),
        ),
        migrations.CreateModel(
            name='ContactGroupCondition',
            fields=[
                ('contextcondition_ptr', models.OneToOneField(primary_key=True, to='campaigns.ContextCondition', parent_link=True, serialize=False, auto_created=True)),
                ('contact_groups', models.ManyToManyField(verbose_name='contact groups', to='shoop.ContactGroup')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.contextcondition',),
        ),
        migrations.CreateModel(
            name='ProductFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(primary_key=True, to='campaigns.CatalogFilter', parent_link=True, serialize=False, auto_created=True)),
                ('products', models.ManyToManyField(verbose_name='product', to='shoop.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter',),
        ),
        migrations.CreateModel(
            name='ProductsInBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(primary_key=True, to='campaigns.BasketCondition', parent_link=True, serialize=False, auto_created=True)),
                ('products', models.ManyToManyField(to='shoop.Product', verbose_name='products', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='ProductTypeFilter',
            fields=[
                ('catalogfilter_ptr', models.OneToOneField(primary_key=True, to='campaigns.CatalogFilter', parent_link=True, serialize=False, auto_created=True)),
                ('product_types', models.ManyToManyField(verbose_name='product Types', to='shoop.ProductType')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.catalogfilter',),
        ),
        migrations.AddField(
            model_name='contextcondition',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_campaigns.contextcondition_set+', null=True, editable=False, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='catalogfilter',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_campaigns.catalogfilter_set+', null=True, editable=False, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='conditions',
            field=models.ManyToManyField(related_name='campaign', to='campaigns.ContextCondition', blank=True),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='created_by',
            field=models.ForeignKey(related_name='+', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, verbose_name='created by', blank=True),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='filters',
            field=models.ManyToManyField(related_name='campaign', to='campaigns.CatalogFilter', blank=True),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='modified_by',
            field=models.ForeignKey(related_name='+', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, verbose_name='modified by', blank=True),
        ),
        migrations.AddField(
            model_name='catalogcampaign',
            name='shop',
            field=models.ForeignKey(help_text='The shop where campaign is active.', verbose_name='shop', to='shoop.Shop'),
        ),
        migrations.AddField(
            model_name='basketcondition',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_campaigns.basketcondition_set+', null=True, editable=False, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='conditions',
            field=models.ManyToManyField(related_name='campaign', to='campaigns.BasketCondition', blank=True),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='coupon',
            field=models.ForeignKey(related_name='campaign', null=True, to='campaigns.Coupon', blank=True),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='created_by',
            field=models.ForeignKey(related_name='+', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, verbose_name='created by', blank=True),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='modified_by',
            field=models.ForeignKey(related_name='+', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, verbose_name='modified by', blank=True),
        ),
        migrations.AddField(
            model_name='basketcampaign',
            name='shop',
            field=models.ForeignKey(help_text='The shop where campaign is active.', verbose_name='shop', to='shoop.Shop'),
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
