# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields
from django.conf import settings
import enumfields.fields
import shuup.utils.analog


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shuup', '0005_shopproduct_visibilty'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.Attribute', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CarrierLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.Carrier', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CompanyContactLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.CompanyContact', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ContactGroupLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.ContactGroup', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CustomerTaxGroupLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.CustomerTaxGroup', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ManufacturerLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.Manufacturer', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderLineLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.OrderLine', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderLineTaxLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.OrderLineTax', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaymentLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.Payment', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaymentMethodLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.PaymentMethod', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaymentProcessorLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.PaymentProcessor', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PersonContactLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.PersonContact', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductMediaLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.ProductMedia', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SavedAddressLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.SavedAddress', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShipmentLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.Shipment', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShipmentProductLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.ShipmentProduct', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShippingMethodLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.ShippingMethod', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShopLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.Shop', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShopProductLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.ShopProduct', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SuppliedProductLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.SuppliedProduct', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SupplierLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.Supplier', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TaxClassLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.TaxClass', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TaxLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('message', models.CharField(max_length=256, verbose_name='message')),
                ('identifier', models.CharField(blank=True, max_length=64, verbose_name='identifier')),
                ('kind', enumfields.fields.EnumIntegerField(default=0, verbose_name='log entry kind', enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True, verbose_name='extra data')),
                ('target', models.ForeignKey(verbose_name='target', to='shuup.Tax', related_name='log_entries', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
