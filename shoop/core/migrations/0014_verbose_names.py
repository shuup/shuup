# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import shoop.core.models
import shoop.utils.analog
from django.conf import settings
import shoop.core.models._shipments
import jsonfield.fields
import enumfields.fields
import shoop.core.fields
import timezone_field.fields
import shoop.core.models._shops


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0013_address_changes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attribute',
            name='searchable',
            field=models.BooleanField(verbose_name='searchable', default=True),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='type',
            field=enumfields.fields.EnumIntegerField(verbose_name='type', enum=shoop.core.models.AttributeType, default=20),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='visibility_mode',
            field=enumfields.fields.EnumIntegerField(verbose_name='visibility mode', enum=shoop.core.models.AttributeVisibility, default=1),
        ),
        migrations.AlterField(
            model_name='attributetranslation',
            name='name',
            field=models.CharField(verbose_name='name', max_length=64),
        ),
        migrations.AlterField(
            model_name='category',
            name='shops',
            field=models.ManyToManyField(verbose_name='shops', blank=True, to='shoop.Shop', related_name='categories'),
        ),
        migrations.AlterField(
            model_name='categorylogentry',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='categorylogentry',
            name='extra',
            field=jsonfield.fields.JSONField(verbose_name='extra data', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='categorylogentry',
            name='identifier',
            field=models.CharField(verbose_name='identifier', blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='categorylogentry',
            name='kind',
            field=enumfields.fields.EnumIntegerField(verbose_name='log entry kind', enum=shoop.utils.analog.LogEntryKind, default=0),
        ),
        migrations.AlterField(
            model_name='categorylogentry',
            name='message',
            field=models.CharField(verbose_name='message', max_length=256),
        ),
        migrations.AlterField(
            model_name='categorylogentry',
            name='target',
            field=models.ForeignKey(verbose_name='target', related_name='log_entries', to='shoop.Category'),
        ),
        migrations.AlterField(
            model_name='categorylogentry',
            name='user',
            field=models.ForeignKey(verbose_name='user', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='companycontact',
            name='members',
            field=models.ManyToManyField(verbose_name='members', blank=True, to='shoop.Contact', related_name='company_memberships'),
        ),
        migrations.AlterField(
            model_name='companycontact',
            name='tax_number',
            field=models.CharField(verbose_name='tax number', blank=True, help_text='e.g. EIN in US or VAT code in Europe', max_length=32),
        ),
        migrations.AlterField(
            model_name='configurationitem',
            name='shop',
            field=models.ForeignKey(verbose_name='shop', blank=True, null=True, related_name='+', to='shoop.Shop'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='is_active',
            field=models.BooleanField(db_index=True, verbose_name='active', default=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='tax_group',
            field=models.ForeignKey(verbose_name='tax group', blank=True, null=True, to='shoop.CustomerTaxGroup', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='contact',
            name='timezone',
            field=timezone_field.fields.TimeZoneField(verbose_name='time zone', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='counter',
            name='id',
            field=enumfields.fields.EnumIntegerField(verbose_name='identifier', enum=shoop.core.models.CounterType, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='counter',
            name='value',
            field=models.IntegerField(verbose_name='value', default=0),
        ),
        migrations.AlterField(
            model_name='immutableaddress',
            name='postal_code',
            field=models.CharField(verbose_name='postal code', blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='immutableaddress',
            name='tax_number',
            field=models.CharField(verbose_name='tax number', blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='mutableaddress',
            name='postal_code',
            field=models.CharField(verbose_name='postal code', blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='mutableaddress',
            name='tax_number',
            field=models.CharField(verbose_name='tax number', blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='order',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='currency',
            field=shoop.core.fields.CurrencyField(verbose_name='currency', max_length=4),
        ),
        migrations.AlterField(
            model_name='order',
            name='deleted',
            field=models.BooleanField(db_index=True, verbose_name='deleted', default=False),
        ),
        migrations.AlterField(
            model_name='order',
            name='display_currency',
            field=shoop.core.fields.CurrencyField(verbose_name='display currency', blank=True, max_length=4),
        ),
        migrations.AlterField(
            model_name='order',
            name='display_currency_rate',
            field=models.DecimalField(verbose_name='display currency rate', decimal_places=9, max_digits=36, default=1),
        ),
        migrations.AlterField(
            model_name='order',
            name='extra_data',
            field=jsonfield.fields.JSONField(verbose_name='extra data', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_data',
            field=jsonfield.fields.JSONField(verbose_name='payment data', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='prices_include_tax',
            field=models.BooleanField(verbose_name='prices include tax'),
        ),
        migrations.AlterField(
            model_name='order',
            name='shipping_data',
            field=jsonfield.fields.JSONField(verbose_name='shipping data', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='shop',
            field=shoop.core.fields.UnsavedForeignKey(verbose_name='shop', to='shoop.Shop', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='order',
            name='tax_number',
            field=models.CharField(verbose_name='tax number', blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='orderline',
            name='extra_data',
            field=jsonfield.fields.JSONField(verbose_name='extra data', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='orderlogentry',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='orderlogentry',
            name='extra',
            field=jsonfield.fields.JSONField(verbose_name='extra data', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='orderlogentry',
            name='identifier',
            field=models.CharField(verbose_name='identifier', blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='orderlogentry',
            name='kind',
            field=enumfields.fields.EnumIntegerField(verbose_name='log entry kind', enum=shoop.utils.analog.LogEntryKind, default=0),
        ),
        migrations.AlterField(
            model_name='orderlogentry',
            name='message',
            field=models.CharField(verbose_name='message', max_length=256),
        ),
        migrations.AlterField(
            model_name='orderlogentry',
            name='target',
            field=models.ForeignKey(verbose_name='target', related_name='log_entries', to='shoop.Order'),
        ),
        migrations.AlterField(
            model_name='orderlogentry',
            name='user',
            field=models.ForeignKey(verbose_name='user', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='orderstatus',
            name='default',
            field=models.BooleanField(db_index=True, verbose_name='default', default=False),
        ),
        migrations.AlterField(
            model_name='orderstatus',
            name='ordering',
            field=models.IntegerField(db_index=True, verbose_name='ordering', default=0),
        ),
        migrations.AlterField(
            model_name='orderstatus',
            name='role',
            field=enumfields.fields.EnumIntegerField(db_index=True, verbose_name='role', default=0, enum=shoop.core.models.OrderStatusRole),
        ),
        migrations.AlterField(
            model_name='orderstatustranslation',
            name='name',
            field=models.CharField(verbose_name='name', max_length=64),
        ),
        migrations.AlterField(
            model_name='payment',
            name='amount_value',
            field=shoop.core.fields.MoneyValueField(verbose_name='amount', decimal_places=9, max_digits=36),
        ),
        migrations.AlterField(
            model_name='payment',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='description',
            field=models.CharField(verbose_name='description', blank=True, max_length=256),
        ),
        migrations.AlterField(
            model_name='payment',
            name='foreign_amount_value',
            field=shoop.core.fields.MoneyValueField(max_digits=36, blank=True, null=True, verbose_name='foreign amount', decimal_places=9, default=None),
        ),
        migrations.AlterField(
            model_name='payment',
            name='foreign_currency',
            field=shoop.core.fields.CurrencyField(verbose_name='foreign amount currency', blank=True, max_length=4, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='gateway_id',
            field=models.CharField(verbose_name='gateway ID', max_length=32),
        ),
        migrations.AlterField(
            model_name='payment',
            name='order',
            field=models.ForeignKey(verbose_name='order', related_name='payments', to='shoop.Order', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payment_identifier',
            field=models.CharField(verbose_name='identifier', unique=True, max_length=96),
        ),
        migrations.AlterField(
            model_name='paymentmethod',
            name='module_data',
            field=jsonfield.fields.JSONField(verbose_name='module data', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='persistentcacheentry',
            name='data',
            field=jsonfield.fields.JSONField(verbose_name='data'),
        ),
        migrations.AlterField(
            model_name='persistentcacheentry',
            name='key',
            field=models.CharField(verbose_name='key', max_length=64),
        ),
        migrations.AlterField(
            model_name='persistentcacheentry',
            name='module',
            field=models.CharField(verbose_name='module', max_length=64),
        ),
        migrations.AlterField(
            model_name='persistentcacheentry',
            name='time',
            field=models.DateTimeField(verbose_name='time', auto_now=True),
        ),
        migrations.AlterField(
            model_name='personcontact',
            name='birth_date',
            field=models.DateField(verbose_name='birth date', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='personcontact',
            name='gender',
            field=enumfields.fields.EnumField(verbose_name='gender', enum=shoop.core.models.Gender, max_length=4, default='u'),
        ),
        migrations.AlterField(
            model_name='personcontact',
            name='user',
            field=models.OneToOneField(verbose_name='user', blank=True, null=True, related_name='contact', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='product',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='deleted',
            field=models.BooleanField(db_index=True, verbose_name='deleted', editable=False, default=False),
        ),
        migrations.AlterField(
            model_name='product',
            name='mode',
            field=enumfields.fields.EnumIntegerField(verbose_name='mode', enum=shoop.core.models.ProductMode, default=0),
        ),
        migrations.AlterField(
            model_name='product',
            name='modified_on',
            field=models.DateTimeField(verbose_name='modified on', auto_now=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='primary_image',
            field=models.ForeignKey(verbose_name='primary image', blank=True, null=True, related_name='primary_image_for_products', to='shoop.ProductMedia', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='productattribute',
            name='attribute',
            field=models.ForeignKey(verbose_name='attribute', to='shoop.Attribute'),
        ),
        migrations.AlterField(
            model_name='productattribute',
            name='datetime_value',
            field=models.DateTimeField(verbose_name='datetime value', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='productattribute',
            name='numeric_value',
            field=models.DecimalField(verbose_name='numeric value', decimal_places=9, max_digits=36, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='productattribute',
            name='product',
            field=models.ForeignKey(verbose_name='product', related_name='attributes', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='productattribute',
            name='untranslated_string_value',
            field=models.TextField(verbose_name='untranslated value', blank=True),
        ),
        migrations.AlterField(
            model_name='productattributetranslation',
            name='translated_string_value',
            field=models.TextField(verbose_name='translated value', blank=True),
        ),
        migrations.AlterField(
            model_name='productcrosssell',
            name='product1',
            field=models.ForeignKey(verbose_name='primary product', related_name='cross_sell_1', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='productcrosssell',
            name='product2',
            field=models.ForeignKey(verbose_name='secondary product', related_name='cross_sell_2', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='productcrosssell',
            name='type',
            field=enumfields.fields.EnumIntegerField(verbose_name='type', enum=shoop.core.models.ProductCrossSellType),
        ),
        migrations.AlterField(
            model_name='productcrosssell',
            name='weight',
            field=models.IntegerField(verbose_name='weight', default=0),
        ),
        migrations.AlterField(
            model_name='productlogentry',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='productlogentry',
            name='extra',
            field=jsonfield.fields.JSONField(verbose_name='extra data', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='productlogentry',
            name='identifier',
            field=models.CharField(verbose_name='identifier', blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='productlogentry',
            name='kind',
            field=enumfields.fields.EnumIntegerField(verbose_name='log entry kind', enum=shoop.utils.analog.LogEntryKind, default=0),
        ),
        migrations.AlterField(
            model_name='productlogentry',
            name='message',
            field=models.CharField(verbose_name='message', max_length=256),
        ),
        migrations.AlterField(
            model_name='productlogentry',
            name='target',
            field=models.ForeignKey(verbose_name='target', related_name='log_entries', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='productlogentry',
            name='user',
            field=models.ForeignKey(verbose_name='user', null=True, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='productmedia',
            name='ordering',
            field=models.IntegerField(verbose_name='ordering', default=0),
        ),
        migrations.AlterField(
            model_name='productmedia',
            name='product',
            field=models.ForeignKey(verbose_name='product', related_name='media', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='productmedia',
            name='shops',
            field=models.ManyToManyField(verbose_name='shops', related_name='product_media', to='shoop.Shop'),
        ),
        migrations.AlterField(
            model_name='productpackagelink',
            name='child',
            field=models.ForeignKey(verbose_name='child product', related_name='+', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='productpackagelink',
            name='parent',
            field=models.ForeignKey(verbose_name='parent product', related_name='+', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='productpackagelink',
            name='quantity',
            field=shoop.core.fields.QuantityField(verbose_name='quantity', decimal_places=9, max_digits=36, default=1),
        ),
        migrations.AlterField(
            model_name='productvariationresult',
            name='combination_hash',
            field=models.CharField(db_index=True, verbose_name='combination hash', unique=True, max_length=40),
        ),
        migrations.AlterField(
            model_name='productvariationresult',
            name='product',
            field=models.ForeignKey(verbose_name='product', related_name='variation_result_supers', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='productvariationresult',
            name='result',
            field=models.ForeignKey(verbose_name='result', related_name='variation_result_subs', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='productvariationresult',
            name='status',
            field=enumfields.fields.EnumIntegerField(db_index=True, verbose_name='status', default=1, enum=shoop.core.models.ProductVariationLinkStatus),
        ),
        migrations.AlterField(
            model_name='productvariationvariable',
            name='product',
            field=models.ForeignKey(verbose_name='product', related_name='variation_variables', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='productvariationvariablevalue',
            name='variable',
            field=models.ForeignKey(verbose_name='variation variable', related_name='values', to='shoop.ProductVariationVariable'),
        ),
        migrations.AlterField(
            model_name='salesunittranslation',
            name='name',
            field=models.CharField(verbose_name='name', max_length=128),
        ),
        migrations.AlterField(
            model_name='salesunittranslation',
            name='short_name',
            field=models.CharField(verbose_name='short name', max_length=128),
        ),
        migrations.AlterField(
            model_name='savedaddress',
            name='owner',
            field=models.ForeignKey(verbose_name='owner', to='shoop.Contact'),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='description',
            field=models.CharField(verbose_name='description', blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='order',
            field=models.ForeignKey(verbose_name='order', related_name='shipments', to='shoop.Order', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='status',
            field=enumfields.fields.EnumIntegerField(verbose_name='status', enum=shoop.core.models._shipments.ShipmentStatus, default=0),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='supplier',
            field=models.ForeignKey(verbose_name='supplier', related_name='shipments', to='shoop.Supplier', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='volume',
            field=shoop.core.fields.MeasurementField(verbose_name='volume', decimal_places=9, max_digits=36, unit='m3', default=0),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='weight',
            field=shoop.core.fields.MeasurementField(verbose_name='weight', decimal_places=9, max_digits=36, unit='kg', default=0),
        ),
        migrations.AlterField(
            model_name='shipmentproduct',
            name='product',
            field=models.ForeignKey(verbose_name='product', related_name='shipments', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='shipmentproduct',
            name='quantity',
            field=shoop.core.fields.QuantityField(verbose_name='quantity', decimal_places=9, max_digits=36, default=0),
        ),
        migrations.AlterField(
            model_name='shipmentproduct',
            name='shipment',
            field=models.ForeignKey(verbose_name='shipment', related_name='products', to='shoop.Shipment', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='shipmentproduct',
            name='unit_volume',
            field=shoop.core.fields.MeasurementField(verbose_name='unit volume', decimal_places=9, max_digits=36, unit='m3', default=0),
        ),
        migrations.AlterField(
            model_name='shipmentproduct',
            name='unit_weight',
            field=shoop.core.fields.MeasurementField(verbose_name='unit weight', decimal_places=9, max_digits=36, unit='g', default=0),
        ),
        migrations.AlterField(
            model_name='shippingmethod',
            name='module_data',
            field=jsonfield.fields.JSONField(verbose_name='module data', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='shop',
            name='currency',
            field=shoop.core.fields.CurrencyField(verbose_name='currency', max_length=4, default=shoop.core.models._shops._get_default_currency),
        ),
        migrations.AlterField(
            model_name='shop',
            name='domain',
            field=models.CharField(verbose_name='domain', unique=True, blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='shop',
            name='options',
            field=jsonfield.fields.JSONField(verbose_name='options', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='shop',
            name='owner',
            field=models.ForeignKey(verbose_name='contact', blank=True, null=True, to='shoop.Contact', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='shop',
            name='prices_include_tax',
            field=models.BooleanField(verbose_name='prices include tax', default=True),
        ),
        migrations.AlterField(
            model_name='shop',
            name='status',
            field=enumfields.fields.EnumIntegerField(verbose_name='status', enum=shoop.core.models.ShopStatus, default=0),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='default_price_value',
            field=shoop.core.fields.MoneyValueField(verbose_name='default price', decimal_places=9, max_digits=36, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='limit_payment_methods',
            field=models.BooleanField(verbose_name='limited for payment methods', default=False),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='limit_shipping_methods',
            field=models.BooleanField(verbose_name='limited for shipping methods', default=False),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='listed',
            field=models.BooleanField(db_index=True, verbose_name='listed', default=True),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='product',
            field=shoop.core.fields.UnsavedForeignKey(verbose_name='product', related_name='shop_products', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='purchasable',
            field=models.BooleanField(db_index=True, verbose_name='purchasable', default=True),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='searchable',
            field=models.BooleanField(db_index=True, verbose_name='searchable', default=True),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='shop',
            field=models.ForeignKey(verbose_name='shop', related_name='shop_products', to='shoop.Shop'),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='shop_primary_image',
            field=models.ForeignKey(verbose_name='primary image', blank=True, null=True, related_name='primary_image_for_shop_products', to='shoop.ProductMedia', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='suppliers',
            field=models.ManyToManyField(verbose_name='suppliers', blank=True, to='shoop.Supplier', related_name='shop_products'),
        ),
        migrations.AlterField(
            model_name='shopproduct',
            name='visible',
            field=models.BooleanField(db_index=True, verbose_name='visible', default=True),
        ),
        migrations.AlterField(
            model_name='shoptranslation',
            name='maintenance_message',
            field=models.CharField(verbose_name='maintenance message', blank=True, max_length=300),
        ),
        migrations.AlterField(
            model_name='shoptranslation',
            name='name',
            field=models.CharField(verbose_name='name', max_length=64),
        ),
        migrations.AlterField(
            model_name='shoptranslation',
            name='public_name',
            field=models.CharField(verbose_name='public name', max_length=64),
        ),
        migrations.AlterField(
            model_name='suppliedproduct',
            name='product',
            field=models.ForeignKey(verbose_name='product', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='suppliedproduct',
            name='supplier',
            field=models.ForeignKey(verbose_name='supplier', to='shoop.Supplier'),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='module_data',
            field=jsonfield.fields.JSONField(verbose_name='module data', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='name',
            field=models.CharField(verbose_name='name', max_length=64),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='stock_managed',
            field=models.BooleanField(verbose_name='stock managed', default=False),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='type',
            field=enumfields.fields.EnumIntegerField(verbose_name='supplier type', enum=shoop.core.models.SupplierType, default=1),
        ),
    ]
