# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_countries.fields
import shuup.core.utils.name_mixin
import django.db.models.deletion
import shuup.core.models._base
import shuup.core.fields
import shuup.utils.models


def copy_order_addresses(apps, schema_editor):
    """
    For orders old shipping and billing address foreign keys is saved
    to mutable_billing_address and mutable_shipping_address. Get or create
    new immutable addresses based on those fields and set those to order
    billing_address and shipping_address.
    """
    order_cls = apps.get_model("shuup", "Order")
    immutable_address_cls = apps.get_model("shuup", "ImmutableAddress")

    for order in order_cls.objects.all():
        if order.mutable_billing_address:
            order.billing_address = immutable_address_cls.objects.get_or_create(
                **shuup.utils.models.get_data_dict(order.mutable_billing_address))[0]

        if order.mutable_shipping_address:
            order.shipping_address = immutable_address_cls.objects.get_or_create(
                **shuup.utils.models.get_data_dict(order.mutable_shipping_address))[0]

        if order.mutable_billing_address or order.mutable_shipping_address:
            order.save()


class FakeAlterField(migrations.AlterField):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0012_add_configurations'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImmutableAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('prefix', models.CharField(max_length=64, verbose_name='name prefix', blank=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('suffix', models.CharField(max_length=64, verbose_name='name suffix', blank=True)),
                ('name_ext', models.CharField(max_length=255, verbose_name='name extension', blank=True)),
                ('company_name', models.CharField(max_length=255, verbose_name='company name', blank=True)),
                ('tax_number', models.CharField(max_length=64, verbose_name='Tax number', blank=True)),
                ('phone', models.CharField(max_length=64, verbose_name='phone', blank=True)),
                ('email', models.EmailField(max_length=128, verbose_name='email', blank=True)),
                ('street', models.CharField(max_length=255, verbose_name='street')),
                ('street2', models.CharField(max_length=255, verbose_name='street (2)', blank=True)),
                ('street3', models.CharField(max_length=255, verbose_name='street (3)', blank=True)),
                ('postal_code', models.CharField(max_length=64, verbose_name='ZIP / Postal code', blank=True)),
                ('city', models.CharField(max_length=255, verbose_name='city')),
                ('region_code', models.CharField(max_length=16, verbose_name='region code', blank=True)),
                ('region', models.CharField(max_length=64, verbose_name='region', blank=True)),
                ('country', django_countries.fields.CountryField(max_length=2, verbose_name='country')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'address',
                'verbose_name_plural': 'addresses',
            },
            bases=(shuup.core.models._base.ChangeProtected, shuup.core.utils.name_mixin.NameMixin, models.Model),
        ),
        migrations.RenameField(
            model_name='order',
            old_name='billing_address',
            new_name='mutable_billing_address',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='shipping_address',
            new_name='mutable_shipping_address',
        ),
        migrations.AddField(
            model_name='order',
            name='billing_address',
            field=models.ForeignKey(related_name='billing_orders', on_delete=django.db.models.deletion.PROTECT, verbose_name='billing address', blank=True, to='shuup.ImmutableAddress', null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_address',
            field=models.ForeignKey(related_name='shipping_orders', on_delete=django.db.models.deletion.PROTECT, verbose_name='shipping address', blank=True, to='shuup.ImmutableAddress', null=True),
        ),
        migrations.RemoveField(
            model_name='address',
            name='is_immutable',
        ),
        migrations.RunPython(copy_order_addresses),
        migrations.RemoveField(
            model_name='order',
            name='mutable_billing_address',
        ),
        migrations.RemoveField(
            model_name='order',
            name='mutable_shipping_address',
        ),
        migrations.RenameModel(
            old_name='Address',
            new_name='MutableAddress'
        ),
        FakeAlterField(
            model_name='contact',
            name='default_billing_address',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, verbose_name='billing address', blank=True, to='shuup.MutableAddress', null=True),
        ),
        FakeAlterField(
            model_name='contact',
            name='default_shipping_address',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, verbose_name='shipping address', blank=True, to='shuup.MutableAddress', null=True),
        ),
        FakeAlterField(
            model_name='savedaddress',
            name='address',
            field=models.ForeignKey(related_name='saved_addresses', verbose_name='address', to='shuup.MutableAddress'),
        )
    ]
