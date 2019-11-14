# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal

import django.core.validators
import django.db.models.deletion
import django_countries.fields
import enumfields.fields
import filer.fields.file
import filer.fields.image
import jsonfield.fields
import mptt.fields
import parler.models
import timezone_field.fields
from django.conf import settings
from django.db import migrations, models

import shuup.core.fields
import shuup.core.models
import shuup.core.modules.interface
import shuup.core.pricing
import shuup.core.taxing
import shuup.core.utils.line_unit_mixin
import shuup.utils.migrations
import shuup.core.utils.name_mixin
import shuup.utils.analog
import shuup.utils.properties

LANGUAGE_CHOICES = [
    (code, code)
    for code in sorted(shuup.core.fields.LanguageFieldMixin.LANGUAGE_CODES)
]


def ensure_default_currencies_exists(apps, schema_editor):
    Currency = apps.get_model("shuup", "Currency")
    default_currencies = [("USD", 2), ("EUR", 2), ("BRL", 2), ("JPY", 0),
                          ("CNY", 2), ("GBP", 2)]
    for code, decimal_places in default_currencies:
        cur, created = Currency.objects.get_or_create(code=code)
        if created:
            cur.decimal_places = decimal_places
            cur.save()


class Migration(migrations.Migration):
    replaces = [
        ('shuup', '0001_initial'),
        ('shuup', '0002_rounding'),
        ('shuup', '0003_shopproduct_backorder_maximum'),
        ('shuup', '0004_update_orderline_refunds'),
        ('shuup', '0005_shopproduct_visibilty'),
        ('shuup', '0006_logmodels'),
        ('shuup', '0007_shop_languages_config'),
        ('shuup', '0008_blank_slugs_for_product'),
        ('shuup', '0009_update_tax_name_max_length'),
        ('shuup', '0010_update_managers'),
        ('shuup', '0011_remove_product_category'),
        ('shuup', '0012_contact_language'),
        ('shuup', '0013_product_shipping_mode_default'),
        ('shuup', '0014_order_status'),
        ('shuup', '0015_shipment_type'),
        ('shuup', '0016_currency'),
        ('shuup', '0017_ensure_currencies_exists'),
        ('shuup', '0018_visibility_defaults'),
        ('shuup', '0019_order_total_limit_behavior_component'),
        ('shuup', '0020_md_to_html'),
        ('shuup', '0021_country_limit_behavior_component'),
        ('shuup', '0022_add_favicon'),
        ('shuup', '0023_category_menu_visibility'),
        ('shuup', '0024_product_shop_description'),
        ('shuup', '0025_product_variation_ordering'),
        ('shuup', '0026_address_geolocation'),
        ('shuup', '0027_modify_shop_fields'),
        ('shuup', '0028_displayunit'),
        ('shuup', '0029_personcontact_names'),
        ('shuup', '0030_add_db_indices'),
        ('shuup', '0031_basket'),
        ('shuup', '0032_shop_product_fields'),
        ('shuup', '0033_order_modified_date'),
        ('shuup', '0034_shops_for_supplier'),
        ('shuup', '0035_remove_shop_permissions'),
        ('shuup', '0036_shop_contacts'),
        ('shuup', '0037_modified_on_contact'),
        ('shuup', '0038_order_date_index'),
        ('shuup', '0039_alter_names'),
    ]

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('filer', '0002_auto_20150606_2003'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=False,
                    editable=False,
                    max_length=64,
                    null=False)),
                ('searchable', models.BooleanField(
                    help_text=
                    'Searchable attributes will be used for product lookup when customers search your store.',
                    verbose_name='searchable',
                    default=True)),
                ('type', enumfields.fields.EnumIntegerField(
                    help_text=
                    'The attribute data type. Attribute values can be set on the product editor page.',
                    verbose_name='type',
                    enum=shuup.core.models.AttributeType,
                    default=20)),
                ('visibility_mode', enumfields.fields.EnumIntegerField(
                    help_text=
                    'Select the attribute visibility setting. Attributes can be shown on the product detail page or can be used to enhance product search results.',
                    verbose_name='visibility mode',
                    enum=shuup.core.models.AttributeVisibility,
                    default=1)),
            ],
            options={
                'verbose_name': 'attribute',
                'verbose_name_plural': 'attributes',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='AttributeLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Attribute',
                    related_name='log_entries',
                    verbose_name='target',
                    on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='AttributeTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'The attribute name. Product attributes can be used to list the various features of a product and can be shown on the product detail page. The product attributes for a product are determined by the product type and can be set on the product editor page.',
                    verbose_name='name',
                    max_length=64)),
                ('master', models.ForeignKey(
                    to='shuup.Attribute',
                    related_name='translations',
                    editable=False,
                    null=True,
                    on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'attribute Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_attribute_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='Basket',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('key', models.CharField(
                    verbose_name='key',
                    unique=True,
                    db_index=True,
                    max_length=32,
                    default=shuup.core.models._basket.generate_key)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on',
                    db_index=True,
                    auto_now_add=True)),
                ('updated_on', models.DateTimeField(
                    verbose_name='updated on', db_index=True, auto_now=True)),
                ('persistent', models.BooleanField(
                    verbose_name='persistent', db_index=True, default=False)),
                ('deleted', models.BooleanField(
                    verbose_name='deleted', db_index=True, default=False)),
                ('finished', models.BooleanField(
                    verbose_name='finished', db_index=True, default=False)),
                ('title', models.CharField(
                    verbose_name='title', max_length=64, blank=True)),
                ('data', shuup.core.fields.TaggedJSONField(
                    verbose_name='data')),
                ('taxless_total_price_value',
                 shuup.core.fields.MoneyValueField(
                     decimal_places=9,
                     max_digits=36,
                     blank=True,
                     verbose_name='taxless total price',
                     null=True,
                     default=0)),
                ('taxful_total_price_value', shuup.core.fields.MoneyValueField(
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    verbose_name='taxful total price',
                    null=True,
                    default=0)),
                ('currency', shuup.core.fields.CurrencyField(
                    verbose_name='currency', max_length=4)),
                ('prices_include_tax', models.BooleanField(
                    verbose_name='prices include tax')),
                ('product_count', models.IntegerField(
                    verbose_name='product_count', default=0)),
                ('creator', models.ForeignKey(
                    related_name='core_baskets_created',
                    to=settings.AUTH_USER_MODEL,
                    blank=True,
                    verbose_name='creator',
                    null=True,
                    on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'basket',
                'verbose_name_plural': 'baskets',
            },
            bases=(shuup.utils.properties.MoneyPropped, models.Model),),
        migrations.CreateModel(
            name='CarrierLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('status', enumfields.fields.EnumIntegerField(
                    help_text=
                    'Here you can choose whether or not you want the category to be visible in your store.',
                    db_index=True,
                    verbose_name='status',
                    enum=shuup.core.models.CategoryStatus,
                    default=1)),
                ('ordering', models.IntegerField(
                    help_text=
                    'You can set the order of categories in your store numerically.',
                    verbose_name='ordering',
                    default=0)),
                ('visibility', enumfields.fields.EnumIntegerField(
                    help_text=
                    'You can choose to limit who sees your category based on whether they are logged in or if they are  part of a customer group.',
                    db_index=True,
                    verbose_name='visibility limitations',
                    enum=shuup.core.models.CategoryVisibility,
                    default=1)),
                ('visible_in_menu', models.BooleanField(
                    help_text=
                    'Check this if this category should be visible in menu.',
                    verbose_name='visible in menu',
                    default=True)),
                ('lft', models.PositiveIntegerField(
                    db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(
                    db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(
                    db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(
                    db_index=True, editable=False)),
                ('image', filer.fields.image.FilerImageField(
                    help_text='Category image. Will be shown at theme.',
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='filer.Image',
                    blank=True,
                    verbose_name='image',
                    null=True)),
                ('parent', mptt.fields.TreeForeignKey(
                    help_text=
                    'If your category is a sub-category of another category, you can link them here.',
                    related_name='children',
                    to='shuup.Category',
                    blank=True,
                    verbose_name='parent category',
                    null=True,
                    on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
                'ordering': ('tree_id', 'lft'),
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='CategoryLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Category',
                    related_name='log_entries',
                    verbose_name='target',
                    on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='CategoryTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'Enter a descriptive name for your product category. Products can be found in menus and in search in your store under the category name.',
                    verbose_name='name',
                    max_length=128)),
                ('description', models.TextField(
                    help_text=
                    'Give your product category a detailed description. This will help shoppers find your products under that category in your store and on the web.',
                    verbose_name='description',
                    blank=True)),
                ('slug', models.SlugField(
                    help_text=
                    'Enter a URL slug for your category. This is what your product category page URL will be. A default will be created using the category name.',
                    blank=True,
                    verbose_name='slug',
                    null=True)),
                ('master', models.ForeignKey(
                    to='shuup.Category',
                    related_name='translations',
                    editable=False,
                    null=True,
                    on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'category Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_category_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='CompanyContactLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ConfigurationItem',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('key', models.CharField(verbose_name='key', max_length=100)),
                ('value', jsonfield.fields.JSONField(verbose_name='value')),
            ],
            options={
                'verbose_name': 'configuration item',
                'verbose_name_plural': 'configuration items',
            },),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    db_index=True,
                    auto_now=True,
                    verbose_name='modified on',
                    null=True)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('is_active', models.BooleanField(
                    help_text=
                    'Check this if the contact is an active customer.',
                    verbose_name='active',
                    db_index=True,
                    default=True)),
                ('_language', shuup.core.fields.LanguageField(
                    help_text=
                    'The primary language to be used in all communications with the contact.',
                    verbose_name='language',
                    choices=LANGUAGE_CHOICES,
                    max_length=10,
                    blank=True)),
                ('marketing_permission', models.BooleanField(
                    help_text=
                    'Check this if the contact can receive marketing and promotional materials.',
                    verbose_name='marketing permission',
                    default=True)),
                ('phone', models.CharField(
                    help_text='The primary phone number of the contact.',
                    verbose_name='phone',
                    max_length=64,
                    blank=True)),
                ('www', models.URLField(
                    help_text='The web address of the contact, if any.',
                    verbose_name='web address',
                    max_length=128,
                    blank=True)),
                ('timezone', timezone_field.fields.TimeZoneField(
                    help_text=
                    'The timezone in which the contact resides. This can be used to target the delivery of promotional materials at a particular time.',
                    blank=True,
                    verbose_name='time zone',
                    null=True)),
                ('prefix', models.CharField(
                    help_text=
                    'The name prefix of the contact. For example, Mr, Mrs, Dr, etc.',
                    verbose_name='name prefix',
                    max_length=64,
                    blank=True)),
                ('name', models.CharField(
                    help_text='The contact name',
                    verbose_name='name',
                    max_length=256)),
                ('suffix', models.CharField(
                    help_text=
                    'The name suffix of the contact. For example, Sr, Jr, etc.',
                    verbose_name='name suffix',
                    max_length=64,
                    blank=True)),
                ('name_ext', models.CharField(
                    verbose_name='name extension', max_length=256,
                    blank=True)),
                ('email', models.EmailField(
                    help_text=
                    'The email that will receive order confirmations and promotional materials (if permitted).',
                    verbose_name='email',
                    max_length=256,
                    blank=True)),
                ('merchant_notes', models.TextField(
                    help_text=
                    'Enter any private notes for this customer that are only accessible in Shuup admin.',
                    verbose_name='merchant notes',
                    blank=True)),
            ],
            options={
                'verbose_name': 'contact',
                'verbose_name_plural': 'contacts',
            },),
        migrations.CreateModel(
            name='ContactGroup',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('show_pricing', models.BooleanField(
                    verbose_name='show as pricing option', default=True)),
                ('show_prices_including_taxes', models.NullBooleanField(
                    verbose_name='show prices including taxes', default=None)),
                ('hide_prices', models.NullBooleanField(
                    verbose_name='hide prices', default=None)),
            ],
            options={
                'verbose_name': 'contact group',
                'verbose_name_plural': 'contact groups',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='ContactGroupLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.ContactGroup',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ContactGroupTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'The contact group name. Contact groups can be used to target sales and campaigns to specific set of users.',
                    verbose_name='name',
                    max_length=64)),
                ('master', models.ForeignKey(
                    to='shuup.ContactGroup',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'contact group Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_contactgroup_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', enumfields.fields.EnumIntegerField(
                    verbose_name='identifier',
                    primary_key=True,
                    serialize=False,
                    enum=shuup.core.models.CounterType)),
                ('value', models.IntegerField(verbose_name='value',
                                              default=0)),
            ],
            options={
                'verbose_name': 'counter',
                'verbose_name_plural': 'counters',
            },),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('code', models.CharField(
                    help_text='The ISO-4217 code of the currency',
                    verbose_name='code',
                    unique=True,
                    max_length=3,
                    validators=[django.core.validators.MinLengthValidator(3)
                                ])),
                ('decimal_places', models.PositiveSmallIntegerField(
                    help_text=
                    'The number of decimal places supported by this currency.',
                    verbose_name='decimal places',
                    validators=[django.core.validators.MaxValueValidator(10)],
                    default=2)),
            ],
            options={
                'verbose_name': 'currency',
                'verbose_name_plural': 'currencies',
            },),
        migrations.CreateModel(
            name='CurrencyLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Currency',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='CustomerTaxGroup',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('enabled', models.BooleanField(
                    verbose_name='enabled', default=True)),
            ],
            options={
                'verbose_name': 'customer tax group',
                'verbose_name_plural': 'customer tax groups',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='CustomerTaxGroupLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.CustomerTaxGroup',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='CustomerTaxGroupTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'The customer tax group name. Customer tax groups can be used to control how taxes are applied to a set of customers. ',
                    verbose_name='name',
                    max_length=100)),
                ('master', models.ForeignKey(
                    to='shuup.CustomerTaxGroup',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'customer tax group Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_customertaxgroup_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='DisplayUnit',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('ratio', shuup.core.fields.QuantityField(
                    help_text=
                    'Size of the display unit in internal unit.  E.g. if internal unit is kilogram and display unit is gram, ratio is 0.001.',
                    decimal_places=9,
                    validators=[
                        shuup.core.models._units.validate_positive_not_zero
                    ],
                    verbose_name='ratio',
                    default=1,
                    max_digits=36)),
                ('decimals', models.PositiveSmallIntegerField(
                    help_text=
                    'The number of decimal places to use for values in the display unit.  The internal values are still rounded based on settings of the internal unit.',
                    verbose_name='decimal places',
                    default=0)),
                ('comparison_value', shuup.core.fields.QuantityField(
                    help_text=
                    'Value to use when displaying unit prices.  E.g. if the display unit is g and the comparison value is 100, then unit prices are shown per 100g, like: $2.95 per 100g.',
                    decimal_places=9,
                    validators=[
                        shuup.core.models._units.validate_positive_not_zero
                    ],
                    verbose_name='comparison value',
                    default=1,
                    max_digits=36)),
                ('allow_bare_number', models.BooleanField(
                    help_text=
                    "If true, values of this unit can be shown without the symbol occasionally.  Usually wanted if the unit is a piece, so that product listings can show just '$5.95' rather than '$5.95 per pc.'.",
                    verbose_name='allow bare number',
                    default=False)),
                ('default', models.BooleanField(
                    help_text=
                    'Use this display unit by default when displaying values of the internal unit.',
                    verbose_name='use by default',
                    default=False)),
            ],
            options={
                'verbose_name': 'display unit',
                'verbose_name_plural': 'display units',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='DisplayUnitTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text='Name of the display unit, e.g. Grams.',
                    verbose_name='name',
                    max_length=150)),
                ('symbol', models.CharField(
                    help_text=
                    "An abbreviated name of the display unit, e.g. 'g'.",
                    verbose_name='symbol',
                    max_length=50)),
                ('master', models.ForeignKey(
                    to='shuup.DisplayUnit',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'display unit Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_displayunit_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='FixedCostBehaviorComponentTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('description', models.CharField(
                    help_text=
                    'The order line text to display when this behavior is applied.',
                    verbose_name='description',
                    max_length=100,
                    blank=True)),
            ],
            options={
                'verbose_name': 'fixed cost behavior component Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_fixedcostbehaviorcomponent_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='ImmutableAddress',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('prefix', models.CharField(
                    help_text=
                    'The name prefix. For example, Mr, Mrs, Ms, Dr, etc.',
                    verbose_name='name prefix',
                    max_length=64,
                    blank=True)),
                ('name', models.CharField(
                    help_text='The name for the address.',
                    verbose_name='name',
                    max_length=255)),
                ('suffix', models.CharField(
                    help_text='The name suffix. For example, Jr, Sr, etc.',
                    verbose_name='name suffix',
                    max_length=64,
                    blank=True)),
                ('name_ext', models.CharField(
                    help_text=
                    'Any other text to display along with the address. This could be department names (for companies) or titles (for people).',
                    verbose_name='name extension',
                    max_length=255,
                    blank=True)),
                ('company_name', models.CharField(
                    help_text='The company name for the address.',
                    verbose_name='company name',
                    max_length=255,
                    blank=True)),
                ('tax_number', models.CharField(
                    help_text=
                    'The business tax number. For example, EIN in US or VAT code in Europe.',
                    verbose_name='tax number',
                    max_length=64,
                    blank=True)),
                ('phone', models.CharField(
                    help_text='The primary phone number for the address.',
                    verbose_name='phone',
                    max_length=64,
                    blank=True)),
                ('email', models.EmailField(
                    help_text='The primary email for the address.',
                    verbose_name='email',
                    max_length=128,
                    blank=True)),
                ('street', models.CharField(
                    help_text='The street address.',
                    verbose_name='street',
                    max_length=255)),
                ('street2', models.CharField(
                    help_text='An additional street address line.',
                    verbose_name='street (2)',
                    max_length=255,
                    blank=True)),
                ('street3', models.CharField(
                    help_text='Any additional street address line.',
                    verbose_name='street (3)',
                    max_length=255,
                    blank=True)),
                ('postal_code', models.CharField(
                    help_text='The address postal/zip code.',
                    verbose_name='postal code',
                    max_length=64,
                    blank=True)),
                ('city', models.CharField(
                    help_text='The address city.',
                    verbose_name='city',
                    max_length=255)),
                ('region_code', models.CharField(
                    help_text='The address region, province, or state.',
                    verbose_name='region code',
                    max_length=16,
                    blank=True)),
                ('region', models.CharField(
                    help_text='The address region, province, or state.',
                    verbose_name='region',
                    max_length=64,
                    blank=True)),
                ('country', django_countries.fields.CountryField(
                    help_text='The address country.',
                    verbose_name='country',
                    max_length=2)),
                ('longitude', models.DecimalField(
                    decimal_places=6, null=True, max_digits=9, blank=True)),
                ('latitude', models.DecimalField(
                    decimal_places=6, null=True, max_digits=9, blank=True)),
            ],
            options={
                'verbose_name': 'address',
                'verbose_name_plural': 'addresses',
                'abstract': False,
            },
            bases=(shuup.core.models._base.ChangeProtected,
                   shuup.core.utils.name_mixin.NameMixin, models.Model),),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='added', auto_now_add=True)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('name', models.CharField(
                    help_text=
                    'Enter the manufacturer’s name. Products can be filtered by the manufacturer and can be useful for inventory and stock management.',
                    verbose_name='name',
                    max_length=128)),
                ('url', models.CharField(
                    help_text=
                    "Enter the URL of the product manufacturer if you would like customers to be able to visit the manufacturer's website.",
                    verbose_name='URL',
                    max_length=128,
                    null=True,
                    blank=True)),
            ],
            options={
                'verbose_name': 'manufacturer',
                'verbose_name_plural': 'manufacturers',
            },),
        migrations.CreateModel(
            name='ManufacturerLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Manufacturer',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='MutableAddress',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('prefix', models.CharField(
                    help_text=
                    'The name prefix. For example, Mr, Mrs, Ms, Dr, etc.',
                    verbose_name='name prefix',
                    max_length=64,
                    blank=True)),
                ('name', models.CharField(
                    help_text='The name for the address.',
                    verbose_name='name',
                    max_length=255)),
                ('suffix', models.CharField(
                    help_text='The name suffix. For example, Jr, Sr, etc.',
                    verbose_name='name suffix',
                    max_length=64,
                    blank=True)),
                ('name_ext', models.CharField(
                    help_text=
                    'Any other text to display along with the address. This could be department names (for companies) or titles (for people).',
                    verbose_name='name extension',
                    max_length=255,
                    blank=True)),
                ('company_name', models.CharField(
                    help_text='The company name for the address.',
                    verbose_name='company name',
                    max_length=255,
                    blank=True)),
                ('tax_number', models.CharField(
                    help_text=
                    'The business tax number. For example, EIN in US or VAT code in Europe.',
                    verbose_name='tax number',
                    max_length=64,
                    blank=True)),
                ('phone', models.CharField(
                    help_text='The primary phone number for the address.',
                    verbose_name='phone',
                    max_length=64,
                    blank=True)),
                ('email', models.EmailField(
                    help_text='The primary email for the address.',
                    verbose_name='email',
                    max_length=128,
                    blank=True)),
                ('street', models.CharField(
                    help_text='The street address.',
                    verbose_name='street',
                    max_length=255)),
                ('street2', models.CharField(
                    help_text='An additional street address line.',
                    verbose_name='street (2)',
                    max_length=255,
                    blank=True)),
                ('street3', models.CharField(
                    help_text='Any additional street address line.',
                    verbose_name='street (3)',
                    max_length=255,
                    blank=True)),
                ('postal_code', models.CharField(
                    help_text='The address postal/zip code.',
                    verbose_name='postal code',
                    max_length=64,
                    blank=True)),
                ('city', models.CharField(
                    help_text='The address city.',
                    verbose_name='city',
                    max_length=255)),
                ('region_code', models.CharField(
                    help_text='The address region, province, or state.',
                    verbose_name='region code',
                    max_length=16,
                    blank=True)),
                ('region', models.CharField(
                    help_text='The address region, province, or state.',
                    verbose_name='region',
                    max_length=64,
                    blank=True)),
                ('country', django_countries.fields.CountryField(
                    help_text='The address country.',
                    verbose_name='country',
                    max_length=2)),
                ('longitude', models.DecimalField(
                    decimal_places=6, null=True, max_digits=9, blank=True)),
                ('latitude', models.DecimalField(
                    decimal_places=6, null=True, max_digits=9, blank=True)),
            ],
            options={
                'verbose_name': 'address',
                'verbose_name_plural': 'addresses',
                'abstract': False,
            },
            bases=(shuup.core.utils.name_mixin.NameMixin, models.Model),),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    verbose_name='modified on', db_index=True, auto_now=True)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    db_index=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('label', models.CharField(
                    verbose_name='label', db_index=True, max_length=32)),
                ('key', models.CharField(
                    verbose_name='key', unique=True, max_length=32)),
                ('reference_number', models.CharField(
                    unique=True,
                    db_index=True,
                    blank=True,
                    verbose_name='reference number',
                    max_length=64,
                    null=True)),
                ('tax_number', models.CharField(
                    verbose_name='tax number', max_length=20, blank=True)),
                ('phone', models.CharField(
                    verbose_name='phone', max_length=64, blank=True)),
                ('email', models.EmailField(
                    verbose_name='email address', max_length=128, blank=True)),
                ('deleted', models.BooleanField(
                    verbose_name='deleted', db_index=True, default=False)),
                ('payment_status', enumfields.fields.EnumIntegerField(
                    verbose_name='payment status',
                    db_index=True,
                    default=0,
                    enum=shuup.core.models.PaymentStatus)),
                ('shipping_status', enumfields.fields.EnumIntegerField(
                    verbose_name='shipping status',
                    db_index=True,
                    default=0,
                    enum=shuup.core.models.ShippingStatus)),
                ('payment_method_name', models.CharField(
                    verbose_name='payment method name',
                    max_length=100,
                    default='',
                    blank=True)),
                ('payment_data', jsonfield.fields.JSONField(
                    verbose_name='payment data', null=True, blank=True)),
                ('shipping_method_name', models.CharField(
                    verbose_name='shipping method name',
                    max_length=100,
                    default='',
                    blank=True)),
                ('shipping_data', jsonfield.fields.JSONField(
                    verbose_name='shipping data', null=True, blank=True)),
                ('extra_data', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('taxful_total_price_value', shuup.core.fields.MoneyValueField(
                    verbose_name='grand total',
                    decimal_places=9,
                    editable=False,
                    max_digits=36,
                    default=0)),
                ('taxless_total_price_value',
                 shuup.core.fields.MoneyValueField(
                     verbose_name='taxless total',
                     decimal_places=9,
                     editable=False,
                     max_digits=36,
                     default=0)),
                ('currency', shuup.core.fields.CurrencyField(
                    verbose_name='currency', max_length=4)),
                ('prices_include_tax', models.BooleanField(
                    verbose_name='prices include tax')),
                ('display_currency', shuup.core.fields.CurrencyField(
                    verbose_name='display currency', max_length=4,
                    blank=True)),
                ('display_currency_rate', models.DecimalField(
                    verbose_name='display currency rate',
                    decimal_places=9,
                    max_digits=36,
                    default=1)),
                ('ip_address', models.GenericIPAddressField(
                    verbose_name='IP address', null=True, blank=True)),
                ('order_date', models.DateTimeField(
                    verbose_name='order date', db_index=True, editable=False)),
                ('payment_date', models.DateTimeField(
                    verbose_name='payment date', editable=False, null=True)),
                ('language', shuup.core.fields.LanguageField(
                    verbose_name='language',
                    choices=LANGUAGE_CHOICES,
                    max_length=10,
                    blank=True)),
                ('customer_comment', models.TextField(
                    verbose_name='customer comment', blank=True)),
                ('admin_comment', models.TextField(
                    verbose_name='admin comment/notes', blank=True)),
                ('require_verification', models.BooleanField(
                    verbose_name='requires verification', default=False)),
                ('all_verified', models.BooleanField(
                    verbose_name='all lines verified', default=False)),
                ('marketing_permission', models.BooleanField(
                    verbose_name='marketing permission', default=True)),
                ('_codes', jsonfield.fields.JSONField(
                    verbose_name='codes', null=True, blank=True)),
                ('billing_address', models.ForeignKey(
                    related_name='billing_orders',
                    to='shuup.ImmutableAddress',
                    blank=True,
                    verbose_name='billing address',
                    on_delete=django.db.models.deletion.PROTECT,
                    null=True)),
                ('creator', shuup.core.fields.UnsavedForeignKey(
                    related_name='orders_created',
                    to=settings.AUTH_USER_MODEL,
                    blank=True,
                    verbose_name='creating user',
                    on_delete=django.db.models.deletion.PROTECT,
                    null=True)),
            ],
            options={
                'verbose_name': 'order',
                'verbose_name_plural': 'orders',
                'ordering': ('-id',),
            },
            bases=(shuup.utils.properties.MoneyPropped, models.Model),),
        migrations.CreateModel(
            name='OrderLine',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('ordering', models.IntegerField(
                    verbose_name='ordering', default=0)),
                ('type', enumfields.fields.EnumIntegerField(
                    verbose_name='line type',
                    enum=shuup.core.models.OrderLineType,
                    default=1)),
                ('sku', models.CharField(
                    verbose_name='line SKU', max_length=48, blank=True)),
                ('text', models.CharField(
                    verbose_name='line text', max_length=256)),
                ('accounting_identifier', models.CharField(
                    verbose_name='accounting identifier',
                    max_length=32,
                    blank=True)),
                ('require_verification', models.BooleanField(
                    verbose_name='require verification', default=False)),
                ('verified', models.BooleanField(
                    verbose_name='verified', default=False)),
                ('extra_data', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('quantity', shuup.core.fields.QuantityField(
                    verbose_name='quantity',
                    decimal_places=9,
                    max_digits=36,
                    default=1)),
                ('base_unit_price_value', shuup.core.fields.MoneyValueField(
                    verbose_name='unit price amount (undiscounted)',
                    decimal_places=9,
                    max_digits=36,
                    default=0)),
                ('discount_amount_value', shuup.core.fields.MoneyValueField(
                    verbose_name='total amount of discount',
                    decimal_places=9,
                    max_digits=36,
                    default=0)),
                ('order', shuup.core.fields.UnsavedForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='shuup.Order',
                    related_name='lines',
                    verbose_name='order')),
                ('parent_line', shuup.core.fields.UnsavedForeignKey(
                    related_name='child_lines',
                    to='shuup.OrderLine',
                    blank=True,
                    verbose_name='parent line',
                    on_delete=django.db.models.deletion.PROTECT,
                    null=True)),
            ],
            options={
                'verbose_name': 'order line',
                'verbose_name_plural': 'order lines',
                'abstract': False,
            },
            bases=(shuup.core.utils.line_unit_mixin.LineWithUnit,
                   shuup.utils.properties.MoneyPropped, models.Model,
                   shuup.core.pricing.Priceful),),
        migrations.CreateModel(
            name='OrderLineLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.OrderLine',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='OrderLineTax',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('name', models.CharField(
                    verbose_name='tax name', max_length=200)),
                ('amount_value', shuup.core.fields.MoneyValueField(
                    verbose_name='tax amount', decimal_places=9,
                    max_digits=36)),
                ('base_amount_value', shuup.core.fields.MoneyValueField(
                    help_text='Amount that this tax is calculated from',
                    verbose_name='base amount',
                    decimal_places=9,
                    max_digits=36)),
                ('ordering', models.IntegerField(
                    verbose_name='ordering', default=0)),
                ('order_line', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='shuup.OrderLine',
                    related_name='taxes',
                    verbose_name='order line')),
            ],
            options={
                'ordering': ['ordering'],
            },
            bases=(shuup.utils.properties.MoneyPropped, models.Model,
                   shuup.core.taxing.LineTax),),
        migrations.CreateModel(
            name='OrderLineTaxLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.OrderLineTax',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='OrderLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Order',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='OrderStatus',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    db_index=True,
                    blank=False,
                    max_length=64,
                    editable=False,
                    null=False)),
                ('ordering', models.IntegerField(
                    help_text=
                    'The processing order of statuses. Default is always processed first.',
                    verbose_name='ordering',
                    db_index=True,
                    default=0)),
                ('role', enumfields.fields.EnumIntegerField(
                    help_text=
                    'Role of status. One role can have multiple order statuses.',
                    db_index=True,
                    verbose_name='role',
                    enum=shuup.core.models.OrderStatusRole,
                    default=0)),
                ('default', models.BooleanField(
                    help_text=
                    'Defines if the status should be considered as default.',
                    verbose_name='default',
                    db_index=True,
                    default=False)),
                ('is_active', models.BooleanField(
                    help_text='Define if the status is usable.',
                    verbose_name='is active',
                    db_index=True,
                    default=True)),
            ],
            options={
                'verbose_name': 'order status',
                'verbose_name_plural': 'order statuses',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='OrderStatusTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text='Name of the order status',
                    verbose_name='name',
                    max_length=64)),
                ('public_name', models.CharField(
                    help_text='The name shown for customer in shop front.',
                    verbose_name='public name',
                    max_length=64)),
                ('master', models.ForeignKey(
                    to='shuup.OrderStatus',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'order status Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_orderstatus_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('gateway_id', models.CharField(
                    verbose_name='gateway ID', max_length=32)),
                ('payment_identifier', models.CharField(
                    verbose_name='identifier', unique=True, max_length=96)),
                ('amount_value', shuup.core.fields.MoneyValueField(
                    verbose_name='amount', decimal_places=9, max_digits=36)),
                ('foreign_amount_value', shuup.core.fields.MoneyValueField(
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    verbose_name='foreign amount',
                    null=True,
                    default=None)),
                ('foreign_currency', shuup.core.fields.CurrencyField(
                    verbose_name='foreign amount currency',
                    max_length=4,
                    null=True,
                    default=None,
                    blank=True)),
                ('description', models.CharField(
                    verbose_name='description', max_length=256, blank=True)),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='shuup.Order',
                    related_name='payments',
                    verbose_name='order')),
            ],
            options={
                'verbose_name': 'payment',
                'verbose_name_plural': 'payments',
            },
            bases=(shuup.utils.properties.MoneyPropped, models.Model),),
        migrations.CreateModel(
            name='PaymentLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Payment',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('enabled', models.BooleanField(
                    help_text=
                    'Check this if this service is selectable on checkout.',
                    verbose_name='enabled',
                    default=False)),
                ('choice_identifier', models.CharField(
                    verbose_name='choice identifier',
                    max_length=64,
                    blank=True)),
                ('old_module_identifier', models.CharField(
                    max_length=64, blank=True)),
                ('old_module_data', jsonfield.fields.JSONField(
                    null=True, blank=True)),
            ],
            options={
                'verbose_name': 'payment method',
                'verbose_name_plural': 'payment methods',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='PaymentMethodLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.PaymentMethod',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='PaymentMethodTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'The payment method name. This name is shown to customers on checkout.',
                    verbose_name='name',
                    max_length=100)),
                ('description', models.CharField(
                    help_text=
                    'The payment method description. This description is shown to customers on checkout.',
                    verbose_name='description',
                    max_length=500,
                    blank=True)),
                ('master', models.ForeignKey(
                    to='shuup.PaymentMethod',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'payment method Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_paymentmethod_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='PaymentProcessorLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='PersistentCacheEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('module', models.CharField(
                    verbose_name='module', max_length=64)),
                ('key', models.CharField(verbose_name='key', max_length=64)),
                ('time', models.DateTimeField(
                    verbose_name='time', auto_now=True)),
                ('data', jsonfield.fields.JSONField(verbose_name='data')),
            ],
            options={
                'verbose_name': 'cache entry',
                'verbose_name_plural': 'cache entries',
            },),
        migrations.CreateModel(
            name='PersonContactLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on',
                    db_index=True,
                    auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    verbose_name='modified on', auto_now=True)),
                ('deleted', models.BooleanField(
                    verbose_name='deleted',
                    db_index=True,
                    editable=False,
                    default=False)),
                ('mode', enumfields.fields.EnumIntegerField(
                    verbose_name='mode',
                    enum=shuup.core.models.ProductMode,
                    default=0)),
                ('stock_behavior', enumfields.fields.EnumIntegerField(
                    help_text=
                    'Set to stocked if inventory should be managed within Shuup.',
                    verbose_name='stock',
                    enum=shuup.core.models.StockBehavior,
                    default=0)),
                ('shipping_mode', enumfields.fields.EnumIntegerField(
                    help_text=
                    'Set to shipped if the product requires shipment.',
                    verbose_name='shipping mode',
                    enum=shuup.core.models.ShippingMode,
                    default=1)),
                ('sku', models.CharField(
                    help_text=
                    'Enter a SKU (Stock Keeping Unit) number for your product. This is a product identification code that helps you track it through your inventory. People often use the number by the barcode on the product, but you can set up any numerical system you want to keep track of products.',
                    verbose_name='SKU',
                    unique=True,
                    db_index=True,
                    max_length=128)),
                ('gtin', models.CharField(
                    help_text=
                    'You can enter a Global Trade Item Number. This is typically a 14 digit identification number for all of your trade items. It can often be found by the barcode.',
                    verbose_name='GTIN',
                    max_length=40,
                    blank=True)),
                ('barcode', models.CharField(
                    help_text=
                    'You can enter the barcode number for your product. This is useful for inventory/stock tracking and analysis.',
                    verbose_name='barcode',
                    max_length=40,
                    blank=True)),
                ('accounting_identifier', models.CharField(
                    verbose_name='bookkeeping account',
                    max_length=32,
                    blank=True)),
                ('profit_center', models.CharField(
                    verbose_name='profit center', max_length=32, blank=True)),
                ('cost_center', models.CharField(
                    verbose_name='cost center', max_length=32, blank=True)),
                ('width', shuup.core.fields.MeasurementField(
                    help_text=
                    'Set the measured width of your product or product packaging. This will provide customers with your product size and help with calculating shipping costs.',
                    unit='mm',
                    decimal_places=9,
                    max_digits=36,
                    verbose_name='width (mm)',
                    default=0)),
                ('height', shuup.core.fields.MeasurementField(
                    help_text=
                    'Set the measured height of your product or product packaging. This will provide customers with your product size and help with calculating shipping costs.',
                    unit='mm',
                    decimal_places=9,
                    max_digits=36,
                    verbose_name='height (mm)',
                    default=0)),
                ('depth', shuup.core.fields.MeasurementField(
                    help_text=
                    'Set the measured depth or length of your product or product packaging. This will provide customers with your product size and help with calculating shipping costs.',
                    unit='mm',
                    decimal_places=9,
                    max_digits=36,
                    verbose_name='depth (mm)',
                    default=0)),
                ('net_weight', shuup.core.fields.MeasurementField(
                    help_text=
                    'Set the measured weight of your product WITHOUT its packaging. This will provide customers with your product weight.',
                    unit='g',
                    decimal_places=9,
                    max_digits=36,
                    verbose_name='net weight (g)',
                    default=0)),
                ('gross_weight', shuup.core.fields.MeasurementField(
                    help_text=
                    'Set the measured gross Weight of your product WITH its packaging. This will help with calculating shipping costs.',
                    unit='g',
                    decimal_places=9,
                    max_digits=36,
                    verbose_name='gross weight (g)',
                    default=0)),
                ('manufacturer', models.ForeignKey(
                    help_text=
                    'Select a manufacturer for your product. These are defined in Products Settings - Manufacturers',
                    on_delete=django.db.models.deletion.PROTECT,
                    to='shuup.Manufacturer',
                    blank=True,
                    verbose_name='manufacturer',
                    null=True)),
            ],
            options={
                'verbose_name': 'product',
                'verbose_name_plural': 'products',
                'ordering': ('-id',),
            },
            bases=(shuup.core.taxing.TaxableItem,
                   shuup.core.models._attributes.AttributableMixin,
                   parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='ProductAttribute',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('numeric_value', models.DecimalField(
                    verbose_name='numeric value',
                    decimal_places=9,
                    null=True,
                    max_digits=36,
                    blank=True)),
                ('datetime_value', models.DateTimeField(
                    verbose_name='datetime value', null=True, blank=True)),
                ('untranslated_string_value', models.TextField(
                    verbose_name='untranslated value', blank=True)),
                ('attribute', models.ForeignKey(
                    verbose_name='attribute', to='shuup.Attribute', on_delete=models.CASCADE),),
                ('product', models.ForeignKey(
                    to='shuup.Product',
                    related_name='attributes',
                    verbose_name='product', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'product attribute',
                'verbose_name_plural': 'product attributes',
                'abstract': False,
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='ProductAttributeTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('translated_string_value', models.TextField(
                    verbose_name='translated value', blank=True)),
                ('master', models.ForeignKey(
                    to='shuup.ProductAttribute',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'product attribute Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_productattribute_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='ProductCrossSell',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('weight', models.IntegerField(
                    verbose_name='weight', default=0)),
                ('type', enumfields.fields.EnumIntegerField(
                    verbose_name='type',
                    enum=shuup.core.models.ProductCrossSellType)),
                ('product1', models.ForeignKey(
                    to='shuup.Product',
                    related_name='cross_sell_1',
                    verbose_name='primary product', on_delete=models.CASCADE)),
                ('product2', models.ForeignKey(
                    to='shuup.Product',
                    related_name='cross_sell_2',
                    verbose_name='secondary product', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'cross sell link',
                'verbose_name_plural': 'cross sell links',
            },),
        migrations.CreateModel(
            name='ProductLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Product',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ProductMedia',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    help_text=
                    'Select what type the media is. It can either be a normal file, part of the documentation, or a sample.',
                    db_index=True,
                    verbose_name='kind',
                    enum=shuup.core.models.ProductMediaKind,
                    default=1)),
                ('external_url', models.URLField(
                    help_text=
                    "Enter URL to external file. If this field is filled, the selected media doesn't apply.",
                    verbose_name='URL',
                    null=True,
                    blank=True)),
                ('ordering', models.IntegerField(
                    help_text=
                    'You enter the numerical order that your image will be displayed on your product page.',
                    verbose_name='ordering',
                    default=0)),
                ('enabled', models.BooleanField(
                    verbose_name='enabled', db_index=True, default=True)),
                ('public', models.BooleanField(
                    help_text=
                    'Check this if you would like the image shown on your product page. Checked by default.',
                    verbose_name='public (shown on product page)',
                    default=True)),
                ('purchased', models.BooleanField(
                    help_text=
                    'Select this if you would like the product media shown for completed purchases.',
                    verbose_name='purchased (shown for finished purchases)',
                    default=False)),
                ('file', filer.fields.file.FilerFileField(
                    to='filer.File',
                    blank=True,
                    verbose_name='file',
                    null=True, on_delete=models.CASCADE)),
                ('product', models.ForeignKey(
                    to='shuup.Product',
                    related_name='media',
                    verbose_name='product', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'product attachment',
                'verbose_name_plural': 'product attachments',
                'ordering': ['ordering'],
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='ProductMediaLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.ProductMedia',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ProductMediaTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('title', models.CharField(
                    help_text=
                    'Choose a title for your product media. This will help it be found in your store and on the web.',
                    verbose_name='title',
                    max_length=128,
                    blank=True)),
                ('description', models.TextField(
                    help_text=
                    'Write a description for your product media. This will help it be found in your store and on the web.',
                    verbose_name='description',
                    blank=True)),
                ('master', models.ForeignKey(
                    to='shuup.ProductMedia',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'product attachment Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_productmedia_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='ProductPackageLink',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('quantity', shuup.core.fields.QuantityField(
                    verbose_name='quantity',
                    decimal_places=9,
                    max_digits=36,
                    default=1)),
                ('child', models.ForeignKey(
                    to='shuup.Product',
                    related_name='+',
                    verbose_name='child product', on_delete=models.CASCADE)),
                ('parent', models.ForeignKey(
                    to='shuup.Product',
                    related_name='+',
                    verbose_name='parent product', on_delete=models.CASCADE)),
            ],),
        migrations.CreateModel(
            name='ProductTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'Enter a descriptive name for your product. This will be its title in your store.',
                    verbose_name='name',
                    max_length=256)),
                ('description', models.TextField(
                    help_text=
                    'To make your product stand out, give it an awesome description. This is what will help your shoppers learn about your products. It will also help shoppers find them in the store and on the web.',
                    verbose_name='description',
                    blank=True)),
                ('short_description', models.CharField(
                    help_text=
                    'Enter a short description for your product. The short description will be used to get the attention of your customer with a small but precise description of your product.',
                    verbose_name='short description',
                    max_length=150,
                    blank=True)),
                ('slug', models.SlugField(
                    help_text=
                    'Enter a URL Slug for your product. This is what your product page URL will be. A default will be created using the product name.',
                    blank=True,
                    verbose_name='slug',
                    max_length=255,
                    null=True)),
                ('keywords', models.TextField(
                    help_text=
                    'You can enter keywords that describe your product. This will help your shoppers learn about your products. It will also help shoppers find them in the store and on the web.',
                    verbose_name='keywords',
                    blank=True)),
                ('status_text', models.CharField(
                    help_text=
                    'This text will be shown alongside the product in the shop. It is useful for informing customers of special stock numbers or preorders. (Ex.: "Available in a month")',
                    verbose_name='status text',
                    max_length=128,
                    blank=True)),
                ('variation_name', models.CharField(
                    help_text=
                    'You can enter a name for the variation of your product. This could be for example different colors or versions.',
                    verbose_name='variation name',
                    max_length=128,
                    blank=True)),
                ('master', models.ForeignKey(
                    to='shuup.Product',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'product Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_product_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('attributes', models.ManyToManyField(
                    help_text=
                    'Select attributes that go with your product type. These are defined in Products Settings – Attributes.',
                    verbose_name='attributes',
                    related_name='product_types',
                    to='shuup.Attribute',
                    blank=True)),
            ],
            options={
                'verbose_name': 'product type',
                'verbose_name_plural': 'product types',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='ProductTypeTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'Enter a descriptive name for your product type. Products and attributes for products of this type can be found under this name.',
                    verbose_name='name',
                    max_length=64)),
                ('master', models.ForeignKey(
                    to='shuup.ProductType',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'product type Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_producttype_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='ProductVariationResult',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('combination_hash', models.CharField(
                    verbose_name='combination hash',
                    unique=True,
                    db_index=True,
                    max_length=40)),
                ('status', enumfields.fields.EnumIntegerField(
                    verbose_name='status',
                    db_index=True,
                    default=1,
                    enum=shuup.core.models.ProductVariationLinkStatus)),
                ('product', models.ForeignKey(
                    to='shuup.Product',
                    related_name='variation_result_supers',
                    verbose_name='product', on_delete=models.CASCADE)),
                ('result', models.ForeignKey(
                    to='shuup.Product',
                    related_name='variation_result_subs',
                    verbose_name='result', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'variation result',
                'verbose_name_plural': 'variation results',
            },),
        migrations.CreateModel(
            name='ProductVariationVariable',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('ordering', models.SmallIntegerField(
                    db_index=True, default=0)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=False,
                    blank=True,
                    editable=False,
                    max_length=64,
                    null=True)),
                ('product', models.ForeignKey(
                    to='shuup.Product',
                    related_name='variation_variables',
                    verbose_name='product', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'variation variable',
                'ordering': ('ordering',),
                'verbose_name_plural': 'variation variables',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='ProductVariationVariableTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(verbose_name='name',
                                          max_length=128)),
                ('master', models.ForeignKey(
                    to='shuup.ProductVariationVariable',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'variation variable Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_productvariationvariable_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='ProductVariationVariableValue',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('ordering', models.SmallIntegerField(
                    db_index=True, default=0)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=False,
                    blank=True,
                    editable=False,
                    max_length=64,
                    null=True)),
                ('variable', models.ForeignKey(
                    to='shuup.ProductVariationVariable',
                    related_name='values',
                    verbose_name='variation variable', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'variation value',
                'ordering': ('ordering',),
                'verbose_name_plural': 'variation values',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='ProductVariationVariableValueTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('value', models.CharField(
                    verbose_name='value', max_length=128)),
                ('master', models.ForeignKey(
                    to='shuup.ProductVariationVariableValue',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'variation value Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_productvariationvariablevalue_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='SalesUnit',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('decimals', models.PositiveSmallIntegerField(
                    help_text=
                    'The number of decimal places allowed by this sales unit.Set this to a value greater than zero if products with this sales unit can be sold in fractional quantities',
                    verbose_name='allowed decimal places',
                    default=0)),
            ],
            options={
                'verbose_name': 'sales unit',
                'verbose_name_plural': 'sales units',
            },
            bases=(shuup.core.models._units._ShortNameToSymbol,
                   parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='SalesUnitTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    "The sales unit name to use for products (For example, 'pieces' or 'units'). Sales units can be set for each product through the product editor view.",
                    verbose_name='name',
                    max_length=128)),
                ('symbol', models.CharField(
                    help_text=
                    'An abbreviated name for this sales unit that is shown throughout admin and order invoices.',
                    verbose_name='symbol',
                    max_length=128)),
                ('master', models.ForeignKey(
                    to='shuup.SalesUnit',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'sales unit Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_salesunit_translation',
                'managed': True,
            },
            bases=(shuup.core.models._units._ShortNameToSymbol, models.Model),
        ),
        migrations.CreateModel(
            name='SavedAddress',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('role', enumfields.fields.EnumIntegerField(
                    verbose_name='role',
                    enum=shuup.core.models.SavedAddressRole,
                    default=1)),
                ('status', enumfields.fields.EnumIntegerField(
                    verbose_name='status',
                    enum=shuup.core.models.SavedAddressStatus,
                    default=1)),
                ('title', models.CharField(
                    verbose_name='title', max_length=255, blank=True)),
                ('address', models.ForeignKey(
                    to='shuup.MutableAddress',
                    related_name='saved_addresses',
                    verbose_name='address', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'saved address',
                'verbose_name_plural': 'saved addresses',
                'ordering': ('owner_id', 'role', 'title'),
            },),
        migrations.CreateModel(
            name='SavedAddressLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.SavedAddress',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ServiceBehaviorComponent',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ServiceProvider',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('enabled', models.BooleanField(
                    help_text=
                    'Check this if this service provider can be used when placing orders',
                    verbose_name='enabled',
                    default=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
            managers=(shuup.utils.migrations.get_managers_for_migration())
        ),
        migrations.CreateModel(
            name='ServiceProviderTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text='The service provider name.',
                    verbose_name='name',
                    max_length=100)),
            ],
            options={
                'verbose_name': 'service provider Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_serviceprovider_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('status', enumfields.fields.EnumIntegerField(
                    verbose_name='status',
                    enum=shuup.core.models.ShipmentStatus,
                    default=0)),
                ('tracking_code', models.CharField(
                    verbose_name='tracking code', max_length=64, blank=True)),
                ('description', models.CharField(
                    verbose_name='description', max_length=255, blank=True)),
                ('volume', shuup.core.fields.MeasurementField(
                    verbose_name='volume',
                    unit='m3',
                    decimal_places=9,
                    max_digits=36,
                    default=0)),
                ('weight', shuup.core.fields.MeasurementField(
                    verbose_name='weight',
                    unit='kg',
                    decimal_places=9,
                    max_digits=36,
                    default=0)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('type', enumfields.fields.EnumIntegerField(
                    verbose_name='type',
                    enum=shuup.core.models.ShipmentType,
                    default=0)),
                ('order', models.ForeignKey(
                    related_name='shipments',
                    to='shuup.Order',
                    blank=True,
                    verbose_name='order',
                    on_delete=django.db.models.deletion.PROTECT,
                    null=True)),
            ],
            options={
                'verbose_name': 'shipment',
                'verbose_name_plural': 'shipments',
            },),
        migrations.CreateModel(
            name='ShipmentLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Shipment',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ShipmentProduct',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('quantity', shuup.core.fields.QuantityField(
                    verbose_name='quantity',
                    decimal_places=9,
                    max_digits=36,
                    default=0)),
                ('unit_volume', shuup.core.fields.MeasurementField(
                    verbose_name='unit volume',
                    unit='m3',
                    decimal_places=9,
                    max_digits=36,
                    default=0)),
                ('unit_weight', shuup.core.fields.MeasurementField(
                    verbose_name='unit weight',
                    unit='g',
                    decimal_places=9,
                    max_digits=36,
                    default=0)),
                ('product', models.ForeignKey(
                    to='shuup.Product',
                    related_name='shipments',
                    verbose_name='product', on_delete=models.CASCADE)),
                ('shipment', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='shuup.Shipment',
                    related_name='products',
                    verbose_name='shipment')),
            ],
            options={
                'verbose_name': 'sent product',
                'verbose_name_plural': 'sent products',
            },),
        migrations.CreateModel(
            name='ShipmentProductLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.ShipmentProduct',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ShippingMethod',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('enabled', models.BooleanField(
                    help_text=
                    'Check this if this service is selectable on checkout.',
                    verbose_name='enabled',
                    default=False)),
                ('choice_identifier', models.CharField(
                    verbose_name='choice identifier',
                    max_length=64,
                    blank=True)),
                ('old_module_identifier', models.CharField(
                    max_length=64, blank=True)),
                ('old_module_data', jsonfield.fields.JSONField(
                    null=True, blank=True)),
            ],
            options={
                'verbose_name': 'shipping method',
                'verbose_name_plural': 'shipping methods',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='ShippingMethodLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.ShippingMethod',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ShippingMethodTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'The shipping method name. This name is shown to customers on checkout.',
                    verbose_name='name',
                    max_length=100)),
                ('description', models.CharField(
                    verbose_name='description', max_length=500, blank=True)),
                ('master', models.ForeignKey(
                    to='shuup.ShippingMethod',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'shipping method Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_shippingmethod_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(
                    verbose_name='modified on', db_index=True, auto_now=True)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=128,
                    editable=False,
                    null=True)),
                ('domain', models.CharField(
                    help_text=
                    'Your shop domain name. Use this field to configure the URL that is used to visit your site. Note: this requires additional configuration through your internet domain registrar.',
                    unique=True,
                    blank=True,
                    verbose_name='domain',
                    max_length=128,
                    null=True)),
                ('status', enumfields.fields.EnumIntegerField(
                    help_text=
                    'Your shop status. Disable your shop if it is no longer in use.',
                    verbose_name='status',
                    enum=shuup.core.models.ShopStatus,
                    default=0)),
                ('options', jsonfield.fields.JSONField(
                    verbose_name='options', null=True, blank=True)),
                ('currency', shuup.core.fields.CurrencyField(
                    help_text=
                    'The primary shop currency. This is the currency used when selling your products.',
                    verbose_name='currency',
                    max_length=4,
                    default=shuup.core.models._shops._get_default_currency)),
                ('prices_include_tax', models.BooleanField(
                    help_text=
                    'This option defines whether product prices entered in admin include taxes. Note this behavior can be overridden with contact group pricing.',
                    verbose_name='prices include tax',
                    default=True)),
                ('maintenance_mode', models.BooleanField(
                    help_text=
                    'Check this if you would like to make your shop temporarily unavailable while you do some shop maintenance.',
                    verbose_name='maintenance mode',
                    default=False)),
                ('contact_address', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='shuup.MutableAddress',
                    blank=True,
                    verbose_name='contact address',
                    null=True)),
                ('favicon', filer.fields.image.FilerImageField(
                    help_text=
                    'Shop favicon. Will be shown next to the address on browser.',
                    related_name='shop_favicons',
                    to='filer.Image',
                    blank=True,
                    verbose_name='favicon',
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True)),
                ('logo', filer.fields.image.FilerImageField(
                    help_text='Shop logo. Will be shown at theme.',
                    related_name='shop_logos',
                    to='filer.Image',
                    blank=True,
                    verbose_name='logo',
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True)),
            ],
            options={
                'verbose_name': 'shop',
                'verbose_name_plural': 'shops',
            },
            bases=(shuup.core.models._base.ChangeProtected,
                   parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='ShopLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Shop',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ShopProduct',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('visibility', enumfields.fields.EnumIntegerField(
                    help_text=
                    'Select if you want your product to be seen and found by customers. <p>Not visible: Product will not be shown in your store front or found in search.</p><p>Searchable: Product will be shown in search but not listed on any category page.</p><p>Listed: Product will be shown on category pages but not shown in search results.</p><p>Always Visible: Product will be shown in your store front and found in search.</p>',
                    db_index=True,
                    verbose_name='visibility',
                    enum=shuup.core.models.ShopProductVisibility,
                    default=3)),
                ('purchasable', models.BooleanField(
                    verbose_name='purchasable', db_index=True, default=True)),
                ('visibility_limit', enumfields.fields.EnumIntegerField(
                    help_text=
                    'Select whether you want your product to have special limitations on its visibility in your store. You can make products visible to all, visible to only logged in users, or visible only to certain customer groups.',
                    db_index=True,
                    verbose_name='visibility limitations',
                    enum=shuup.core.models.ProductVisibility,
                    default=1)),
                ('backorder_maximum', shuup.core.fields.QuantityField(
                    help_text=
                    'The number of units that can be purchased after the product is out of stock. Set to blank for product to be purchasable without limits.',
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    verbose_name='backorder maximum',
                    null=True,
                    default=0)),
                ('purchase_multiple', shuup.core.fields.QuantityField(
                    help_text=
                    'Set this if the product needs to be purchased in multiples. For example, if the purchase multiple is set to 2, then customers are required to order the product in multiples of 2.',
                    verbose_name='purchase multiple',
                    decimal_places=9,
                    max_digits=36,
                    default=0)),
                ('minimum_purchase_quantity', shuup.core.fields.QuantityField(
                    help_text=
                    'Set a minimum number of products needed to be ordered for the purchase. This is useful for setting bulk orders and B2B purchases.',
                    verbose_name='minimum purchase',
                    decimal_places=9,
                    max_digits=36,
                    default=1)),
                ('limit_shipping_methods', models.BooleanField(
                    help_text=
                    'Check this if you want to limit your product to use only select payment methods. You can select the payment method(s) in the field below.',
                    verbose_name='limited for shipping methods',
                    default=False)),
                ('limit_payment_methods', models.BooleanField(
                    help_text=
                    'Check this if you want to limit your product to use only select payment methods. You can select the payment method(s) in the field below.',
                    verbose_name='limited for payment methods',
                    default=False)),
                ('default_price_value', shuup.core.fields.MoneyValueField(
                    help_text=
                    'This is the default individual base unit (or multi-pack) price of the product. All discounts or coupons will be based off of this price.',
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    verbose_name='default price',
                    null=True)),
                ('minimum_price_value', shuup.core.fields.MoneyValueField(
                    help_text=
                    'This is the default price that the product cannot go under in your store, despite coupons or discounts being applied. This is useful to make sure your product price stays above cost.',
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    verbose_name='minimum price',
                    null=True)),
                ('categories', models.ManyToManyField(
                    help_text=
                    'Add secondary categories for your product. These are other categories that your product fits under and that it can be found by in your store.',
                    verbose_name='categories',
                    related_name='shop_products',
                    to='shuup.Category',
                    blank=True)),
                ('display_unit', models.ForeignKey(
                    help_text='Unit for displaying quantities of this product',
                    to='shuup.DisplayUnit',
                    blank=True,
                    verbose_name='display unit',
                    null=True, on_delete=models.CASCADE)),
                ('payment_methods', models.ManyToManyField(
                    help_text=
                    'Select the payment methods you would like to limit the product to using. These are defined in Settings - Payment Methods.',
                    verbose_name='payment methods',
                    related_name='payment_products',
                    to='shuup.PaymentMethod',
                    blank=True)),
                ('primary_category', models.ForeignKey(
                    help_text=
                    'Choose the primary category for your product. This will be the main category for classification in the system. Your product can be found under this category in your store. Categories are defined in Products Settings - Categories.',
                    related_name='primary_shop_products',
                    to='shuup.Category',
                    blank=True,
                    verbose_name='primary category',
                    on_delete=django.db.models.deletion.PROTECT,
                    null=True)),
                ('product', shuup.core.fields.UnsavedForeignKey(
                    to='shuup.Product',
                    related_name='shop_products',
                    verbose_name='product', on_delete=models.CASCADE)),
                ('shipping_methods', models.ManyToManyField(
                    help_text=
                    'Select the shipping methods you would like to limit the product to using. These are defined in Settings - Shipping Methods.',
                    verbose_name='shipping methods',
                    related_name='shipping_products',
                    to='shuup.ShippingMethod',
                    blank=True)),
                ('shop', models.ForeignKey(
                    to='shuup.Shop',
                    related_name='shop_products',
                    verbose_name='shop', on_delete=models.CASCADE)),
                ('shop_primary_image', models.ForeignKey(
                    help_text=
                    'Click this to set this image as the primary display image for your product.',
                    related_name='primary_image_for_shop_products',
                    to='shuup.ProductMedia',
                    blank=True,
                    verbose_name='primary image',
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True)),
            ],
            bases=(shuup.utils.properties.MoneyPropped,
                   parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='ShopProductLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.ShopProduct',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='ShopProductTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'Enter a descriptive name for your product. This will be its title in your store.',
                    verbose_name='name',
                    max_length=256,
                    null=True,
                    blank=True)),
                ('description', models.TextField(
                    help_text=
                    'To make your product stand out, give it an awesome description. This is what will help your shoppers learn about your products. It will also help shoppers find them in the store and on the web.',
                    verbose_name='description',
                    null=True,
                    blank=True)),
                ('short_description', models.CharField(
                    help_text=
                    'Enter a short description for your product. The short description will be used to get the attention of your customer with a small but precise description of your product.',
                    verbose_name='short description',
                    max_length=150,
                    null=True,
                    blank=True)),
                ('master', models.ForeignKey(
                    to='shuup.ShopProduct',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'shop product Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_shopproduct_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='ShopTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'The shop name. This name is displayed throughout admin.',
                    verbose_name='name',
                    max_length=64)),
                ('public_name', models.CharField(
                    help_text=
                    'The public shop name. This name is displayed in the store front and in any customer email correspondence.',
                    verbose_name='public name',
                    max_length=64)),
                ('maintenance_message', models.CharField(
                    help_text=
                    'The message to display to customers while your shop is in maintenance mode.',
                    verbose_name='maintenance message',
                    max_length=300,
                    blank=True)),
                ('master', models.ForeignKey(
                    to='shuup.Shop',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'shop Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_shop_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='SuppliedProduct',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('sku', models.CharField(
                    verbose_name='SKU', db_index=True, max_length=128)),
                ('alert_limit', models.IntegerField(
                    verbose_name='alert limit', default=0)),
                ('physical_count', shuup.core.fields.QuantityField(
                    verbose_name='physical stock count',
                    decimal_places=9,
                    editable=False,
                    max_digits=36,
                    default=0)),
                ('logical_count', shuup.core.fields.QuantityField(
                    verbose_name='logical stock count',
                    decimal_places=9,
                    editable=False,
                    max_digits=36,
                    default=0)),
                ('product', models.ForeignKey(
                    verbose_name='product', to='shuup.Product', on_delete=models.CASCADE)),
            ],),
        migrations.CreateModel(
            name='SuppliedProductLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.SuppliedProduct',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('name', models.CharField(
                    help_text=
                    'The product suppliers name. Suppliers can be used manage the inventory of stocked products.',
                    verbose_name='name',
                    max_length=64)),
                ('type', enumfields.fields.EnumIntegerField(
                    help_text=
                    'The supplier type indicates whether the products are supplied through an internal supplier or an external supplier.',
                    verbose_name='supplier type',
                    enum=shuup.core.models.SupplierType,
                    default=1)),
                ('stock_managed', models.BooleanField(
                    help_text=
                    'Check this if this supplier will be used to manage the inventory of stocked products.',
                    verbose_name='stock managed',
                    default=False)),
                ('module_identifier', models.CharField(
                    help_text=
                    'Select the supplier module to use for this supplier. Supplier modules define the rules by which inventory is managed.',
                    verbose_name='module',
                    max_length=64,
                    blank=True)),
                ('module_data', jsonfield.fields.JSONField(
                    verbose_name='module data', null=True, blank=True)),
                ('shops', models.ManyToManyField(
                    help_text=
                    'You can select which shops the supplier is available to.',
                    verbose_name='shops',
                    related_name='suppliers',
                    to='shuup.Shop',
                    blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(shuup.core.modules.interface.ModuleInterface, models.Model),
        ),
        migrations.CreateModel(
            name='SupplierLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Supplier',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='Tax',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('code', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('rate', models.DecimalField(
                    help_text='The percentage rate of the tax.',
                    decimal_places=5,
                    max_digits=6,
                    blank=True,
                    verbose_name='tax rate',
                    null=True)),
                ('amount_value', shuup.core.fields.MoneyValueField(
                    help_text=
                    'The flat amount of the tax. Mutually exclusive with percentage rates.',
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    verbose_name='tax amount value',
                    null=True,
                    default=None)),
                ('currency', shuup.core.fields.CurrencyField(
                    verbose_name='currency of tax amount',
                    max_length=4,
                    null=True,
                    default=None,
                    blank=True)),
                ('enabled', models.BooleanField(
                    help_text='Check this if this tax is valid and active.',
                    verbose_name='enabled',
                    default=True)),
            ],
            options={
                'verbose_name': 'tax',
                'verbose_name_plural': 'taxes',
            },
            bases=(shuup.utils.properties.MoneyPropped,
                   shuup.core.models._base.ChangeProtected,
                   parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='TaxClass',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    unique=True,
                    blank=True,
                    max_length=64,
                    editable=False,
                    null=True)),
                ('enabled', models.BooleanField(
                    help_text=
                    'Check this if this tax class is active and valid.',
                    verbose_name='enabled',
                    default=True)),
            ],
            options={
                'verbose_name': 'tax class',
                'verbose_name_plural': 'tax classes',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='TaxClassLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.TaxClass',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='TaxClassTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'The tax class name. Tax classes are used to control how taxes are applied to products.',
                    verbose_name='name',
                    max_length=100)),
                ('master', models.ForeignKey(
                    to='shuup.TaxClass',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'tax class Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_taxclass_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='TaxLogEntry',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    verbose_name='message', max_length=256)),
                ('identifier', models.CharField(
                    verbose_name='identifier', max_length=64, blank=True)),
                ('kind', enumfields.fields.EnumIntegerField(
                    verbose_name='log entry kind',
                    enum=shuup.utils.analog.LogEntryKind,
                    default=0)),
                ('extra', jsonfield.fields.JSONField(
                    verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(
                    to='shuup.Tax',
                    related_name='log_entries',
                    verbose_name='target', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    null=True)),
            ],
            options={
                'abstract': False,
            },),
        migrations.CreateModel(
            name='TaxTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('name', models.CharField(
                    help_text=
                    'The tax name. This is shown in order lines in order invoices and confirmations.',
                    verbose_name='name',
                    max_length=124)),
                ('master', models.ForeignKey(
                    to='shuup.Tax',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'tax Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_tax_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='WaivingCostBehaviorComponentTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('description', models.CharField(
                    help_text=
                    'The order line text to display when this behavior is applied.',
                    verbose_name='description',
                    max_length=100,
                    blank=True)),
            ],
            options={
                'verbose_name': 'waiving cost behavior component Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_waivingcostbehaviorcomponent_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='WeightBasedPriceRange',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('min_value', shuup.core.fields.MeasurementField(
                    help_text=
                    'The minimum weight, in grams, for this price to apply.',
                    unit='g',
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    verbose_name='min weight (g)',
                    null=True,
                    default=0)),
                ('max_value', shuup.core.fields.MeasurementField(
                    help_text=
                    'The maximum weight, in grams, before this price no longer applies.',
                    unit='g',
                    decimal_places=9,
                    max_digits=36,
                    blank=True,
                    verbose_name='max weight (g)',
                    null=True,
                    default=0)),
                ('price_value', shuup.core.fields.MoneyValueField(
                    help_text=
                    'The cost to apply to this service when the weight criteria is met.',
                    decimal_places=9,
                    max_digits=36)),
            ],
            options={
                'abstract': False,
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='WeightBasedPriceRangeTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True,
                    serialize=False)),
                ('language_code', models.CharField(
                    verbose_name='Language', db_index=True, max_length=15)),
                ('description', models.CharField(
                    help_text=
                    'The order line text to display when this behavior is applied.',
                    verbose_name='description',
                    max_length=100,
                    blank=True)),
                ('master', models.ForeignKey(
                    to='shuup.WeightBasedPriceRange',
                    related_name='translations',
                    editable=False,
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'weight based price range Translation',
                'db_tablespace': '',
                'default_permissions': (),
                'db_table': 'shuup_weightbasedpricerange_translation',
                'managed': True,
            },),
        migrations.CreateModel(
            name='AnonymousContact',
            fields=[
                ('contact_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.Contact',
                    primary_key=True,
                    serialize=False,
                    on_delete=models.CASCADE)),
            ],
            options={
                'managed': False,
            },
            bases=('shuup.contact',),),
        migrations.CreateModel(
            name='Carrier',
            fields=[
                ('serviceprovider_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.ServiceProvider',
                    primary_key=True,
                    serialize=False,
                    on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.serviceprovider',),
            managers=(shuup.utils.migrations.get_managers_for_migration())
        ),
        migrations.CreateModel(
            name='CompanyContact',
            fields=[
                ('contact_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.Contact',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
                ('tax_number', models.CharField(
                    help_text='e.g. EIN in US or VAT code in Europe',
                    verbose_name='tax number',
                    max_length=32,
                    blank=True)),
            ],
            options={
                'verbose_name': 'company',
                'verbose_name_plural': 'companies',
            },
            bases=('shuup.contact',),),
        migrations.CreateModel(
            name='CountryLimitBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.ServiceBehaviorComponent',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
                ('available_in_countries', jsonfield.fields.JSONField(
                    verbose_name='available in countries',
                    null=True,
                    blank=True)),
                ('available_in_european_countries', models.BooleanField(
                    verbose_name='available in european countries',
                    default=False)),
                ('unavailable_in_countries', jsonfield.fields.JSONField(
                    verbose_name='unavailable in countries',
                    null=True,
                    blank=True)),
                ('unavailable_in_european_countries', models.BooleanField(
                    verbose_name='unavailable in european countries',
                    default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),),
        migrations.CreateModel(
            name='FixedCostBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.ServiceBehaviorComponent',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
                ('price_value', shuup.core.fields.MoneyValueField(
                    help_text='The fixed cost to apply to this service.',
                    decimal_places=9,
                    max_digits=36)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',
                   parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='GroupAvailabilityBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.ServiceBehaviorComponent',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),),
        migrations.CreateModel(
            name='OrderTotalLimitBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.ServiceBehaviorComponent',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
                ('min_price_value', shuup.core.fields.MoneyValueField(
                    verbose_name='min price value',
                    decimal_places=9,
                    null=True,
                    max_digits=36,
                    blank=True)),
                ('max_price_value', shuup.core.fields.MoneyValueField(
                    verbose_name='max price value',
                    decimal_places=9,
                    null=True,
                    max_digits=36,
                    blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),),
        migrations.CreateModel(
            name='PaymentProcessor',
            fields=[
                ('serviceprovider_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.ServiceProvider',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.serviceprovider',),
            managers=(shuup.utils.migrations.get_managers_for_migration())
        ),
        migrations.CreateModel(
            name='PersonContact',
            fields=[
                ('contact_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.Contact',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
                ('gender', enumfields.fields.EnumField(
                    help_text='The gender of the contact.',
                    verbose_name='gender',
                    max_length=4,
                    enum=shuup.core.models.Gender,
                    default='u')),
                ('birth_date', models.DateField(
                    help_text='The birth date of the contact.',
                    verbose_name='birth date',
                    null=True,
                    blank=True)),
                ('first_name', models.CharField(
                    help_text='The first name of the contact.',
                    verbose_name='first name',
                    max_length=120,
                    blank=True)),
                ('last_name', models.CharField(
                    help_text='The last name of the contact.',
                    verbose_name='last name',
                    max_length=120,
                    blank=True)),
                ('user', models.OneToOneField(
                    related_name='contact',
                    to=settings.AUTH_USER_MODEL,
                    blank=True,
                    verbose_name='user',
                    null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'person',
                'verbose_name_plural': 'persons',
            },
            bases=('shuup.contact',),),
        migrations.CreateModel(
            name='StaffOnlyBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.ServiceBehaviorComponent',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),),
        migrations.CreateModel(
            name='WaivingCostBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.ServiceBehaviorComponent',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
                ('price_value', shuup.core.fields.MoneyValueField(
                    help_text=
                    'The cost to apply to this service if the total price is below the waive limit.',
                    decimal_places=9,
                    max_digits=36)),
                ('waive_limit_value', shuup.core.fields.MoneyValueField(
                    help_text=
                    'The total price of products at which this service cost is waived.',
                    decimal_places=9,
                    max_digits=36)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',
                   parler.models.TranslatableModelMixin, models.Model),),
        migrations.CreateModel(
            name='WeightBasedPricingBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.ServiceBehaviorComponent',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),),
        migrations.CreateModel(
            name='WeightLimitsBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.ServiceBehaviorComponent',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
                ('min_weight', models.DecimalField(
                    help_text=
                    'The minimum weight required for this service to be available.',
                    decimal_places=6,
                    max_digits=36,
                    blank=True,
                    verbose_name='minimum weight',
                    null=True)),
                ('max_weight', models.DecimalField(
                    help_text='The maximum weight allowed by this service.',
                    decimal_places=6,
                    max_digits=36,
                    blank=True,
                    verbose_name='maximum weight',
                    null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),),
        migrations.AddField(
            model_name='suppliedproduct',
            name='supplier',
            field=models.ForeignKey(
                verbose_name='supplier', to='shuup.Supplier', on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='shopproduct',
            name='suppliers',
            field=models.ManyToManyField(
                help_text=
                'List your suppliers here. Suppliers can be found in Product Settings - Suppliers.',
                verbose_name='suppliers',
                related_name='shop_products',
                to='shuup.Supplier',
                blank=True),),
        migrations.AddField(
            model_name='shopproduct',
            name='visibility_groups',
            field=models.ManyToManyField(
                help_text=
                'Select the groups you would like to make your product visible for. These groups are defined in Contacts Settings - Contact Groups.',
                verbose_name='visible for groups',
                related_name='visible_products',
                to='shuup.ContactGroup',
                blank=True),),
        migrations.AddField(
            model_name='shop',
            name='owner',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                to='shuup.Contact',
                blank=True,
                verbose_name='contact',
                null=True),),
        migrations.AddField(
            model_name='shop',
            name='staff_members',
            field=models.ManyToManyField(
                verbose_name='staff members',
                related_name='_shop_staff_members_+',
                to=settings.AUTH_USER_MODEL,
                blank=True),),
        migrations.AddField(
            model_name='shippingmethod',
            name='behavior_components',
            field=models.ManyToManyField(
                verbose_name='behavior components',
                to='shuup.ServiceBehaviorComponent'),),
        migrations.AddField(
            model_name='shippingmethod',
            name='logo',
            field=filer.fields.image.FilerImageField(
                on_delete=django.db.models.deletion.SET_NULL,
                to='filer.Image',
                blank=True,
                verbose_name='logo',
                null=True),),
        migrations.AddField(
            model_name='shippingmethod',
            name='shop',
            field=models.ForeignKey(
                help_text='The shop for this service.',
                to='shuup.Shop',
                verbose_name='shop', on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='shippingmethod',
            name='tax_class',
            field=models.ForeignKey(
                help_text=
                'The tax class to use for this service. Tax classes are defined in Settings - Tax Classes.',
                on_delete=django.db.models.deletion.PROTECT,
                to='shuup.TaxClass',
                verbose_name='tax class'),),
        migrations.AddField(
            model_name='shipment',
            name='supplier',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='shuup.Supplier',
                related_name='shipments',
                verbose_name='supplier'),),
        migrations.AddField(
            model_name='serviceprovidertranslation',
            name='master',
            field=models.ForeignKey(
                to='shuup.ServiceProvider',
                related_name='base_translations',
                editable=False,
                null=True, on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='serviceprovider',
            name='logo',
            field=filer.fields.image.FilerImageField(
                on_delete=django.db.models.deletion.SET_NULL,
                to='filer.Image',
                blank=True,
                verbose_name='logo',
                null=True),),
        migrations.AddField(
            model_name='serviceprovider',
            name='polymorphic_ctype',
            field=models.ForeignKey(
                to='contenttypes.ContentType',
                related_name='polymorphic_shuup.serviceprovider_set+',
                editable=False,
                null=True, on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='servicebehaviorcomponent',
            name='polymorphic_ctype',
            field=models.ForeignKey(
                to='contenttypes.ContentType',
                related_name='polymorphic_shuup.servicebehaviorcomponent_set+',
                editable=False,
                null=True, on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='savedaddress',
            name='owner',
            field=models.ForeignKey(verbose_name='owner', to='shuup.Contact', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='productmedia',
            name='shops',
            field=models.ManyToManyField(
                help_text=
                'Select which shops you would like the product media to be visible in.',
                verbose_name='shops',
                to='shuup.Shop',
                related_name='product_media'),),
        migrations.AddField(
            model_name='product',
            name='primary_image',
            field=models.ForeignKey(
                related_name='primary_image_for_products',
                to='shuup.ProductMedia',
                blank=True,
                verbose_name='primary image',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True),),
        migrations.AddField(
            model_name='product',
            name='sales_unit',
            field=models.ForeignKey(
                help_text=
                'Select a sales unit for your product. This is shown in your store front and is used to determine whether the product can be purchased using fractional amounts. Sales units are defined in Products - Sales Units.',
                on_delete=django.db.models.deletion.PROTECT,
                to='shuup.SalesUnit',
                blank=True,
                verbose_name='sales unit',
                null=True),),
        migrations.AddField(
            model_name='product',
            name='tax_class',
            field=models.ForeignKey(
                help_text=
                'Select a tax class for your product. The tax class is used to determine which taxes to apply to your product. Tax classes are defined in Settings - Tax Classes. The rules by which taxes are applied are defined in Settings - Tax Rules.',
                on_delete=django.db.models.deletion.PROTECT,
                to='shuup.TaxClass',
                verbose_name='tax class'),),
        migrations.AddField(
            model_name='product',
            name='type',
            field=models.ForeignKey(
                help_text=
                'Select a product type for your product. These allow you to configure custom attributes to help with classification and analysis.',
                related_name='products',
                to='shuup.ProductType',
                verbose_name='product type',
                on_delete=django.db.models.deletion.PROTECT),),
        migrations.AddField(
            model_name='product',
            name='variation_parent',
            field=models.ForeignKey(
                related_name='variation_children',
                to='shuup.Product',
                blank=True,
                verbose_name='variation parent',
                on_delete=django.db.models.deletion.PROTECT,
                null=True),),
        migrations.AlterUniqueTogether(
            name='persistentcacheentry',
            unique_together=set([('module', 'key')]),),
        migrations.AddField(
            model_name='paymentmethod',
            name='behavior_components',
            field=models.ManyToManyField(
                verbose_name='behavior components',
                to='shuup.ServiceBehaviorComponent'),),
        migrations.AddField(
            model_name='paymentmethod',
            name='logo',
            field=filer.fields.image.FilerImageField(
                on_delete=django.db.models.deletion.SET_NULL,
                to='filer.Image',
                blank=True,
                verbose_name='logo',
                null=True),),
        migrations.AddField(
            model_name='paymentmethod',
            name='shop',
            field=models.ForeignKey(
                help_text='The shop for this service.',
                to='shuup.Shop',
                verbose_name='shop', on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='paymentmethod',
            name='tax_class',
            field=models.ForeignKey(
                help_text=
                'The tax class to use for this service. Tax classes are defined in Settings - Tax Classes.',
                on_delete=django.db.models.deletion.PROTECT,
                to='shuup.TaxClass',
                verbose_name='tax class'),),
        migrations.AlterUniqueTogether(
            name='orderstatus',
            unique_together=set([('identifier', 'role')]),),
        migrations.AddField(
            model_name='orderlinetax',
            name='tax',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='shuup.Tax',
                related_name='order_line_taxes',
                verbose_name='tax'),),
        migrations.AddField(
            model_name='orderline',
            name='product',
            field=shuup.core.fields.UnsavedForeignKey(
                related_name='order_lines',
                to='shuup.Product',
                blank=True,
                verbose_name='product',
                on_delete=django.db.models.deletion.PROTECT,
                null=True),),
        migrations.AddField(
            model_name='orderline',
            name='supplier',
            field=shuup.core.fields.UnsavedForeignKey(
                related_name='order_lines',
                to='shuup.Supplier',
                blank=True,
                verbose_name='supplier',
                on_delete=django.db.models.deletion.PROTECT,
                null=True),),
        migrations.AddField(
            model_name='order',
            name='customer',
            field=shuup.core.fields.UnsavedForeignKey(
                related_name='customer_orders',
                to='shuup.Contact',
                blank=True,
                verbose_name='customer',
                on_delete=django.db.models.deletion.PROTECT,
                null=True),),
        migrations.AddField(
            model_name='order',
            name='modified_by',
            field=shuup.core.fields.UnsavedForeignKey(
                related_name='orders_modified',
                to=settings.AUTH_USER_MODEL,
                blank=True,
                verbose_name='modifier user',
                on_delete=django.db.models.deletion.PROTECT,
                null=True),),
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=shuup.core.fields.UnsavedForeignKey(
                related_name='payment_orders',
                to='shuup.PaymentMethod',
                blank=True,
                verbose_name='payment method',
                on_delete=django.db.models.deletion.PROTECT,
                null=True,
                default=None),),
        migrations.AddField(
            model_name='order',
            name='shipping_address',
            field=models.ForeignKey(
                related_name='shipping_orders',
                to='shuup.ImmutableAddress',
                blank=True,
                verbose_name='shipping address',
                on_delete=django.db.models.deletion.PROTECT,
                null=True),),
        migrations.AddField(
            model_name='order',
            name='shipping_method',
            field=shuup.core.fields.UnsavedForeignKey(
                related_name='shipping_orders',
                to='shuup.ShippingMethod',
                blank=True,
                verbose_name='shipping method',
                on_delete=django.db.models.deletion.PROTECT,
                null=True,
                default=None),),
        migrations.AddField(
            model_name='order',
            name='shop',
            field=shuup.core.fields.UnsavedForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='shuup.Shop',
                verbose_name='shop'),),
        migrations.AddField(
            model_name='order',
            name='status',
            field=shuup.core.fields.UnsavedForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='shuup.OrderStatus',
                verbose_name='status'),),
        migrations.AddField(
            model_name='displayunit',
            name='internal_unit',
            field=models.ForeignKey(
                help_text=
                'The sales unit that this display unit is linked to.',
                related_name='display_units',
                to='shuup.SalesUnit',
                verbose_name='internal unit', on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='contactgroup',
            name='members',
            field=models.ManyToManyField(
                verbose_name='members',
                related_name='groups',
                to='shuup.Contact',
                blank=True),),
        migrations.AddField(
            model_name='contact',
            name='default_billing_address',
            field=models.ForeignKey(
                related_name='+',
                to='shuup.MutableAddress',
                blank=True,
                verbose_name='billing address',
                on_delete=django.db.models.deletion.PROTECT,
                null=True),),
        migrations.AddField(
            model_name='contact',
            name='default_payment_method',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                to='shuup.PaymentMethod',
                blank=True,
                verbose_name='default payment method',
                null=True),),
        migrations.AddField(
            model_name='contact',
            name='default_shipping_address',
            field=models.ForeignKey(
                related_name='+',
                to='shuup.MutableAddress',
                blank=True,
                verbose_name='shipping address',
                on_delete=django.db.models.deletion.PROTECT,
                null=True),),
        migrations.AddField(
            model_name='contact',
            name='default_shipping_method',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                to='shuup.ShippingMethod',
                blank=True,
                verbose_name='default shipping method',
                null=True),),
        migrations.AddField(
            model_name='contact',
            name='polymorphic_ctype',
            field=models.ForeignKey(
                to='contenttypes.ContentType',
                related_name='polymorphic_shuup.contact_set+',
                editable=False,
                null=True, on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='contact',
            name='shops',
            field=models.ManyToManyField(
                help_text='Inform which shops have access to this contact.',
                verbose_name='shops',
                to='shuup.Shop',
                blank=True),),
        migrations.AddField(
            model_name='contact',
            name='tax_group',
            field=models.ForeignKey(
                help_text=
                'Select the contact tax group to use for this contact. Tax groups can be used to customize the tax rules the that apply to any of this contacts orders. Tax groups are defined in Settings - Customer Tax Groups and can be applied to tax rules in Settings - Tax Rules',
                on_delete=django.db.models.deletion.PROTECT,
                to='shuup.CustomerTaxGroup',
                blank=True,
                verbose_name='tax group',
                null=True),),
        migrations.AddField(
            model_name='configurationitem',
            name='shop',
            field=models.ForeignKey(
                related_name='+',
                to='shuup.Shop',
                blank=True,
                verbose_name='shop',
                null=True, on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='category',
            name='shops',
            field=models.ManyToManyField(
                help_text=
                'You can select which shops the category is visible in.',
                verbose_name='shops',
                related_name='categories',
                to='shuup.Shop',
                blank=True),),
        migrations.AddField(
            model_name='category',
            name='visibility_groups',
            field=models.ManyToManyField(
                help_text=(
                    'Select the customer groups you would like to be able to '
                    'see the category. These groups are defined in Contacts '
                    'Settings - Contact Groups.'),
                verbose_name='visible for groups',
                related_name='visible_categories',
                to='shuup.ContactGroup',
                blank=True),),
        migrations.AddField(
            model_name='basket',
            name='customer',
            field=models.ForeignKey(
                related_name='customer_core_baskets',
                to='shuup.Contact',
                blank=True,
                verbose_name='customer',
                null=True, on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='basket',
            name='products',
            field=models.ManyToManyField(
                verbose_name='products', to='shuup.Product', blank=True),),
        migrations.AddField(
            model_name='basket',
            name='shop',
            field=models.ForeignKey(verbose_name='shop', to='shuup.Shop', on_delete=models.CASCADE),),
        migrations.CreateModel(
            name='CustomCarrier',
            fields=[
                ('carrier_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.Carrier',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'custom carrier',
                'verbose_name_plural': 'custom carriers',
            },
            bases=('shuup.carrier',),
            managers=(shuup.utils.migrations.get_managers_for_migration())
        ),
        migrations.CreateModel(
            name='CustomPaymentProcessor',
            fields=[
                ('paymentprocessor_ptr', models.OneToOneField(
                    auto_created=True,
                    parent_link=True,
                    to='shuup.PaymentProcessor',
                    primary_key=True,
                    serialize=False, on_delete=models.CASCADE)),
                ('rounding_quantize', models.DecimalField(
                    help_text='Rounding quantize for cash payment.',
                    verbose_name='rounding quantize',
                    decimal_places=9,
                    max_digits=36,
                    default=Decimal('0.05'))),
                ('rounding_mode', enumfields.fields.EnumField(
                    help_text='Rounding mode for cash payment.',
                    verbose_name='rounding mode',
                    max_length=50,
                    enum=shuup.core.models._service_payment.RoundingMode,
                    default='ROUND_HALF_UP')),
            ],
            options={
                'verbose_name': 'custom payment processor',
                'verbose_name_plural': 'custom payment processors',
            },
            bases=('shuup.paymentprocessor',),
            managers=(shuup.utils.migrations.get_managers_for_migration())
        ),
        migrations.AlterUniqueTogether(
            name='weightbasedpricerangetranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AddField(
            model_name='weightbasedpricerange',
            name='component',
            field=models.ForeignKey(
                to='shuup.WeightBasedPricingBehaviorComponent',
                related_name='ranges', on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='waivingcostbehaviorcomponenttranslation',
            name='master',
            field=models.ForeignKey(
                to='shuup.WaivingCostBehaviorComponent',
                related_name='translations',
                editable=False,
                null=True, on_delete=models.CASCADE),),
        migrations.AlterUniqueTogether(
            name='taxtranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='taxclasstranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='suppliedproduct',
            unique_together=set([('supplier', 'product')]),),
        migrations.AlterUniqueTogether(
            name='shoptranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='shopproducttranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='shopproduct',
            unique_together=set([('shop', 'product')]),),
        migrations.AlterUniqueTogether(
            name='shippingmethodtranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AddField(
            model_name='shippingmethod',
            name='carrier',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                to='shuup.Carrier',
                blank=True,
                verbose_name='carrier',
                null=True),
            ),
        migrations.AlterUniqueTogether(
            name='serviceprovidertranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='salesunittranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='productvariationvariablevaluetranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='productvariationvariablevalue',
            unique_together=set([('variable', 'identifier')]),),
        migrations.AlterUniqueTogether(
            name='productvariationvariabletranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='productvariationvariable',
            unique_together=set([('product', 'identifier')]),),
        migrations.AlterUniqueTogether(
            name='producttypetranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='producttranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='productpackagelink',
            unique_together=set([('parent', 'child')]),),
        migrations.AlterUniqueTogether(
            name='productmediatranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='productattributetranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AddField(
            model_name='personcontactlogentry',
            name='target',
            field=models.ForeignKey(
                to='shuup.PersonContact',
                related_name='log_entries',
                verbose_name='target', on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='paymentprocessorlogentry',
            name='target',
            field=models.ForeignKey(
                to='shuup.PaymentProcessor',
                related_name='log_entries',
                verbose_name='target', on_delete=models.CASCADE),),
        migrations.AlterUniqueTogether(
            name='paymentmethodtranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AddField(
            model_name='paymentmethod',
            name='payment_processor',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                to='shuup.PaymentProcessor',
                blank=True,
                verbose_name='payment processor',
                null=True),),
        migrations.AlterUniqueTogether(
            name='orderstatustranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AddField(
            model_name='order',
            name='orderer',
            field=shuup.core.fields.UnsavedForeignKey(
                related_name='orderer_orders',
                to='shuup.PersonContact',
                blank=True,
                verbose_name='orderer',
                on_delete=django.db.models.deletion.PROTECT,
                null=True),),
        migrations.AddField(
            model_name='groupavailabilitybehaviorcomponent',
            name='groups',
            field=models.ManyToManyField(
                help_text=
                'The contact groups for which this service is available.',
                verbose_name='groups',
                to='shuup.ContactGroup'),),
        migrations.AddField(
            model_name='fixedcostbehaviorcomponenttranslation',
            name='master',
            field=models.ForeignKey(
                to='shuup.FixedCostBehaviorComponent',
                related_name='translations',
                editable=False,
                null=True, on_delete=models.CASCADE),),
        migrations.AlterUniqueTogether(
            name='displayunittranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='customertaxgrouptranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='contactgrouptranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AddField(
            model_name='contact',
            name='account_manager',
            field=models.ForeignKey(
                to='shuup.PersonContact',
                blank=True,
                verbose_name='account manager',
                null=True, on_delete=models.CASCADE),),
        migrations.AlterUniqueTogether(
            name='configurationitem',
            unique_together=set([('shop', 'key')]),),
        migrations.AddField(
            model_name='companycontactlogentry',
            name='target',
            field=models.ForeignKey(
                to='shuup.CompanyContact',
                related_name='log_entries',
                verbose_name='target', on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='companycontact',
            name='members',
            field=models.ManyToManyField(
                verbose_name='members',
                related_name='company_memberships',
                to='shuup.Contact',
                blank=True),),
        migrations.AlterUniqueTogether(
            name='categorytranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AddField(
            model_name='carrierlogentry',
            name='target',
            field=models.ForeignKey(
                to='shuup.Carrier',
                related_name='log_entries',
                verbose_name='target', on_delete=models.CASCADE),),
        migrations.AddField(
            model_name='basket',
            name='orderer',
            field=models.ForeignKey(
                related_name='orderer_core_baskets',
                to='shuup.PersonContact',
                blank=True,
                verbose_name='orderer',
                null=True, on_delete=models.CASCADE),),
        migrations.AlterUniqueTogether(
            name='attributetranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='waivingcostbehaviorcomponenttranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.AlterUniqueTogether(
            name='fixedcostbehaviorcomponenttranslation',
            unique_together=set([('language_code', 'master')]),),
        migrations.RunPython(ensure_default_currencies_exists,
                             migrations.RunPython.noop),
    ]
