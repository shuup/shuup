# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import filer.fields.image
import jsonfield.fields
import shuup.core.fields
from shuup.core.models import ShopStatus


def migrate_payment_and_shipping_methods(apps, schema_editor):
    entries = [
        dict(
            model='ShippingMethod',
            module_identifier='default_shipping',
            provider_attr='carrier',
            provider_creator=get_default_carrier,
        ),
        dict(
            model='PaymentMethod',
            module_identifier='default_payment',
            provider_attr='payment_processor',
            provider_creator=get_default_payment_processor,
        ),
    ]
    for entry in entries:
        method_model = apps.get_model("shuup", entry['model'])
        module_identifier = entry['module_identifier']
        provider_attr = entry['provider_attr']
        provider_creator = entry['provider_creator']

        # Set shop for all methods
        methods = method_model.objects.filter(shop=None)
        if methods:
            methods.update(shop=get_default_shop(apps))

        # Migrate methods using the default module
        methods = method_model.objects.filter(
            old_module_identifier__in=set([module_identifier, '']))
        if methods:
            # Set service provider
            methods.update(**{provider_attr: provider_creator(apps)})

            # Migrate module data to behavior components
            for method in methods:
                data = method.old_module_data
                if data:
                    price = data.get('price', 0)
                    waiver = data.get('price_waiver_product_minimum', 0)
                    minw = data.get('min_weight', 0)
                    maxw = data.get('max_weight', 0)
                    if price and not waiver:
                        method.behavior_components.add(
                            create_polymorphic_object(
                                apps, 'FixedCostBehaviorComponent',
                                price_value=price))
                    elif waiver:
                        method.behavior_components.add(
                            create_polymorphic_object(
                                apps, 'WaivingCostBehaviorComponent',
                                price_value=price, waive_limit_value=waiver))
                    if minw or maxw:
                        method.behavior_components.add(
                            create_polymorphic_object(
                                apps, 'WeightLimitsBehaviorComponent',
                                min_weight=minw, max_weight=maxw))

                # Migrate "status" field to "enabled" field
                if method.status:  # 0 = DISABLED, 1 = ENABLED
                    method.enabled = True
                    method.save()


def get_default_carrier(apps):
    return get_or_create_service_provider(apps, "CustomCarrier", "Carrier")


def get_default_payment_processor(apps):
    return get_or_create_service_provider(
        apps, "CustomPaymentProcessor", "Manual payment processing")


def get_or_create_service_provider(apps, model_name, name):
    """
    Create a service provider by model name.

    Also update polymorphic_ctype for the model if needed, see:
    http://django-polymorphic.readthedocs.org/en/latest/migrating.html
    """
    sp_model = apps.get_model("shuup", model_name)
    sp_trans_model = apps.get_model("shuup", "ServiceProviderTranslation")
    identifier = 'default:' + sp_model.__name__.lower()

    (provider, created) = sp_model.objects.get_or_create(identifier=identifier)

    if created:
        sp_trans_model.objects.create(
            master_id=provider.pk, language_code="en", name=name)
        update_polymorphic_ctype(apps, provider)

    return provider


def create_polymorphic_object(apps, model_name, **kwargs):
    model = apps.get_model("shuup", model_name)
    obj = model.objects.create(**kwargs)
    update_polymorphic_ctype(apps, obj)
    return obj


def update_polymorphic_ctype(apps, obj):
    if obj.polymorphic_ctype is None:
        content_type_model = apps.get_model('contenttypes', 'ContentType')
        ctype = content_type_model.objects.get_for_model(obj._meta.model)
        obj.polymorphic_ctype = ctype
        obj.save()


def get_default_shop(apps):
    shop_model = apps.get_model("shuup", "Shop")
    shop = shop_model.objects.filter(identifier="default").first()
    if not shop:
        shop = shop_model.objects.first()
    if not shop:
        shop = shop_model.objects.create(
            identifier="default", status=ShopStatus.DISABLED,
            maintenance_mode=True)
        apps.get_model("shuup", "ShopTranslation").objects.create(
            master_id=shop.pk, language_code="en",
            name="Shop", public_name="Shop")
    return shop


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('filer', '0002_auto_20150606_2003'),
        ('shuup', '0019_contact_merchant_notes'),
    ]

    operations = [
        migrations.CreateModel(
            name='FixedCostBehaviorComponentTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('description', models.CharField(max_length=100, verbose_name='description', blank=True)),
            ],
            options={
                'managed': True,
                'db_table': 'shuup_fixedcostbehaviorcomponent_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'fixed cost behavior component Translation',
            },
        ),
        migrations.CreateModel(
            name='ServiceBehaviorComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceProvider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', shuup.core.fields.InternalIdentifierField(null=True, editable=False, max_length=64, blank=True, unique=True)),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
                ('logo', filer.fields.image.FilerImageField(blank=True, to='filer.Image', verbose_name='logo', on_delete=django.db.models.deletion.SET_NULL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceProviderTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
            ],
            options={
                'managed': True,
                'db_table': 'shuup_serviceprovider_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'service provider Translation',
            },
        ),
        migrations.CreateModel(
            name='WaivingCostBehaviorComponentTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('description', models.CharField(max_length=100, verbose_name='description', blank=True)),
            ],
            options={
                'managed': True,
                'db_table': 'shuup_waivingcostbehaviorcomponent_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'waiving cost behavior component Translation',
            },
        ),
        migrations.RenameField(
            model_name='paymentmethod',
            old_name='module_identifier',
            new_name='old_module_identifier',
        ),
        migrations.RenameField(
            model_name='paymentmethod',
            old_name='module_data',
            new_name='old_module_data',
        ),
        migrations.RenameField(
            model_name='shippingmethod',
            old_name='module_identifier',
            new_name='old_module_identifier',
        ),
        migrations.RenameField(
            model_name='shippingmethod',
            old_name='module_data',
            new_name='old_module_data',
        ),
        migrations.AlterField(
            model_name='paymentmethod',
            name='old_module_data',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='paymentmethod',
            name='old_module_identifier',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='shippingmethod',
            name='old_module_data',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='shippingmethod',
            name='old_module_identifier',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='choice_identifier',
            field=models.CharField(max_length=64, verbose_name='choice identifier', blank=True),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='enabled',
            field=models.BooleanField(default=False, verbose_name='enabled'),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='shop',
            field=models.ForeignKey(verbose_name='shop', blank=True, to='shuup.Shop', null=True),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='logo',
            field=filer.fields.image.FilerImageField(blank=True, to='filer.Image', verbose_name='logo', on_delete=django.db.models.deletion.SET_NULL, null=True),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='choice_identifier',
            field=models.CharField(max_length=64, verbose_name='choice identifier', blank=True),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='enabled',
            field=models.BooleanField(default=False, verbose_name='enabled'),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='shop',
            field=models.ForeignKey(verbose_name='shop', blank=True, to='shuup.Shop', null=True),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='logo',
            field=filer.fields.image.FilerImageField(blank=True, to='filer.Image', verbose_name='logo', on_delete=django.db.models.deletion.SET_NULL, null=True),
        ),
        migrations.AlterField(
            model_name='paymentmethodtranslation',
            name='name',
            field=models.CharField(max_length=100, verbose_name='name'),
        ),
        migrations.AddField(
            model_name='paymentmethodtranslation',
            name='description',
            field=models.CharField(blank=True, max_length=500, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='shippingmethodtranslation',
            name='name',
            field=models.CharField(max_length=100, verbose_name='name'),
        ),
        migrations.AddField(
            model_name='shippingmethodtranslation',
            name='description',
            field=models.CharField(blank=True, max_length=500, verbose_name='description'),
        ),
        migrations.CreateModel(
            name='Carrier',
            fields=[
                ('serviceprovider_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.ServiceProvider')),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.serviceprovider',),
        ),
        migrations.CreateModel(
            name='FixedCostBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.ServiceBehaviorComponent')),
                ('price_value', shuup.core.fields.MoneyValueField(max_digits=36, decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent', models.Model),
        ),
        migrations.CreateModel(
            name='PaymentProcessor',
            fields=[
                ('serviceprovider_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.ServiceProvider')),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.serviceprovider',),
        ),
        migrations.CreateModel(
            name='WaivingCostBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.ServiceBehaviorComponent')),
                ('price_value', shuup.core.fields.MoneyValueField(max_digits=36, decimal_places=9)),
                ('waive_limit_value', shuup.core.fields.MoneyValueField(max_digits=36, decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent', models.Model),
        ),
        migrations.CreateModel(
            name='WeightLimitsBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.ServiceBehaviorComponent')),
                ('min_weight', models.DecimalField(null=True, verbose_name='minimum weight', max_digits=36, decimal_places=6, blank=True)),
                ('max_weight', models.DecimalField(null=True, verbose_name='maximum weight', max_digits=36, decimal_places=6, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),
        ),
        migrations.AddField(
            model_name='serviceprovidertranslation',
            name='master',
            field=models.ForeignKey(related_name='base_translations', editable=False, to='shuup.ServiceProvider', null=True),
        ),
        migrations.AddField(
            model_name='serviceprovider',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_shuup.serviceprovider_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='servicebehaviorcomponent',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_shuup.servicebehaviorcomponent_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='behavior_components',
            field=models.ManyToManyField(to='shuup.ServiceBehaviorComponent', verbose_name='behavior components'),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='behavior_components',
            field=models.ManyToManyField(to='shuup.ServiceBehaviorComponent', verbose_name='behavior components'),
        ),
        migrations.CreateModel(
            name='CustomCarrier',
            fields=[
                ('carrier_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.Carrier')),
            ],
            options={
                'verbose_name': 'custom carrier',
                'verbose_name_plural': 'custom carriers',
            },
            bases=('shuup.carrier',),
        ),
        migrations.CreateModel(
            name='CustomPaymentProcessor',
            fields=[
                ('paymentprocessor_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.PaymentProcessor')),
            ],
            options={
                'verbose_name': 'custom payment processor',
                'verbose_name_plural': 'custom payment processors',
            },
            bases=('shuup.paymentprocessor',),
        ),
        migrations.AddField(
            model_name='waivingcostbehaviorcomponenttranslation',
            name='master',
            field=models.ForeignKey(related_name='translations', editable=False, to='shuup.WaivingCostBehaviorComponent', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='serviceprovidertranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AddField(
            model_name='fixedcostbehaviorcomponenttranslation',
            name='master',
            field=models.ForeignKey(related_name='translations', editable=False, to='shuup.FixedCostBehaviorComponent', null=True),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='payment_processor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='payment processor', blank=True, to='shuup.PaymentProcessor', null=True),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='carrier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='carrier', blank=True, to='shuup.Carrier', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='waivingcostbehaviorcomponenttranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='fixedcostbehaviorcomponenttranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.RunPython(
            migrate_payment_and_shipping_methods,
            migrations.RunPython.noop
        ),
        migrations.RemoveField(
            model_name='paymentmethod',
            name='status',
        ),
        migrations.RemoveField(
            model_name='shippingmethod',
            name='status',
        ),
        migrations.AlterField(
            model_name='paymentmethod',
            name='shop',
            field=models.ForeignKey(to='shuup.Shop', blank=False, null=False, verbose_name='shop'),
        ),
        migrations.AlterField(
            model_name='shippingmethod',
            name='shop',
            field=models.ForeignKey(to='shuup.Shop', blank=False, null=False, verbose_name='shop'),
        ),
    ]
