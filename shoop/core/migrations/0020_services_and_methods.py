# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import filer.fields.image
import jsonfield.fields
import shoop.core.fields
from shoop.core.models import ShopStatus


def create_default_service_providers(apps, schema_editor):
    """
    Create default carrier and payment processor.

    Link existing ShippingMethods and PaymentMethods which use the
    previous default module to the created carrier or payment processor.
    """
    carrier = create_service_provider(apps, "CustomCarrier", "Carrier")
    apps.get_model("shoop", "ShippingMethod").objects.filter(
        old_module_identifier="default_shipping").update(
            carrier=carrier)

    payment_processor = create_service_provider(
        apps, "CustomPaymentProcessor", "Manual payment processing")
    apps.get_model("shoop", "PaymentMethod").objects.filter(
        old_module_identifier="default_payment").update(
            payment_processor=payment_processor)


def create_service_provider(apps, model_name, name):
    """
    Create a service provider by model name.

    Also update polymorphic_ctype for the model if needed, see:
    http://django-polymorphic.readthedocs.org/en/latest/migrating.html
    """
    sp_model = apps.get_model("shoop", model_name)
    sp_trans_model = apps.get_model("shoop", "ServiceProviderTranslation")
    provider = sp_model.objects.create(identifier=sp_model.__name__)
    sp_trans_model.objects.create(
        master_id=provider.pk, language_code="en", name=name)

    # Update polymorphic_ctype
    content_type_model = apps.get_model("contenttypes", "ContentType")
    new_ct = content_type_model.objects.get_for_model(sp_model)
    sp_model.objects.filter(
        polymorphic_ctype__isnull=True).update(polymorphic_ctype=new_ct)

    return provider


def set_shop_for_methods(apps, schema_editor):
    shop = None
    method_models = [
        apps.get_model("shoop", "PaymentMethod"),
        apps.get_model("shoop", "ShippingMethod"),
    ]
    for method_model in method_models:
        methods = method_model.objects.filter(shop=None)
        if methods:
            if not shop:
                shop = get_default_shop(apps)
            methods.update(shop=shop)


def get_default_shop(apps):
    shop_model = apps.get_model("shoop", "Shop")
    shop = shop_model.objects.filter(identifier="default").first()
    if not shop:
        shop = shop_model.objects.first()
    if not shop:
        shop = shop_model.objects.create(
            identifier="default", status=ShopStatus.DISABLED,
            maintenance_mode=True)
        apps.get_model("shoop", "ShopTranslation").objects.create(
            master_id=shop.pk, language_code="en",
            name="Shop", public_name="Shop")
    return shop


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('filer', '0002_auto_20150606_2003'),
        ('shoop', '0019_contact_merchant_notes'),
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
                'db_table': 'shoop_fixedcostbehaviorcomponent_translation',
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
                ('identifier', shoop.core.fields.InternalIdentifierField(null=True, editable=False, max_length=64, blank=True, unique=True)),
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
                'db_table': 'shoop_serviceprovider_translation',
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
                'db_table': 'shoop_waivingcostbehaviorcomponent_translation',
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
            field=models.ForeignKey(verbose_name='shop', blank=True, to='shoop.Shop', null=True),
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
            field=models.ForeignKey(verbose_name='shop', blank=True, to='shoop.Shop', null=True),
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
                ('serviceprovider_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.ServiceProvider')),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.serviceprovider',),
        ),
        migrations.CreateModel(
            name='FixedCostBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.ServiceBehaviorComponent')),
                ('price_value', shoop.core.fields.MoneyValueField(max_digits=36, decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.servicebehaviorcomponent', models.Model),
        ),
        migrations.CreateModel(
            name='PaymentProcessor',
            fields=[
                ('serviceprovider_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.ServiceProvider')),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.serviceprovider',),
        ),
        migrations.CreateModel(
            name='WaivingCostBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.ServiceBehaviorComponent')),
                ('price_value', shoop.core.fields.MoneyValueField(max_digits=36, decimal_places=9)),
                ('waive_limit_value', shoop.core.fields.MoneyValueField(max_digits=36, decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.servicebehaviorcomponent', models.Model),
        ),
        migrations.CreateModel(
            name='WeightLimitsBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.ServiceBehaviorComponent')),
                ('min_weight', models.DecimalField(null=True, verbose_name='minimum weight', max_digits=36, decimal_places=6, blank=True)),
                ('max_weight', models.DecimalField(null=True, verbose_name='maximum weight', max_digits=36, decimal_places=6, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.servicebehaviorcomponent',),
        ),
        migrations.AddField(
            model_name='serviceprovidertranslation',
            name='master',
            field=models.ForeignKey(related_name='base_translations', editable=False, to='shoop.ServiceProvider', null=True),
        ),
        migrations.AddField(
            model_name='serviceprovider',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_shoop.serviceprovider_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='servicebehaviorcomponent',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_shoop.servicebehaviorcomponent_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='behavior_components',
            field=models.ManyToManyField(to='shoop.ServiceBehaviorComponent', verbose_name='behavior components'),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='behavior_components',
            field=models.ManyToManyField(to='shoop.ServiceBehaviorComponent', verbose_name='behavior components'),
        ),
        migrations.CreateModel(
            name='CustomCarrier',
            fields=[
                ('carrier_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.Carrier')),
            ],
            options={
                'verbose_name': 'custom carrier',
                'verbose_name_plural': 'custom carriers',
            },
            bases=('shoop.carrier',),
        ),
        migrations.CreateModel(
            name='CustomPaymentProcessor',
            fields=[
                ('paymentprocessor_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.PaymentProcessor')),
            ],
            options={
                'verbose_name': 'custom payment processor',
                'verbose_name_plural': 'custom payment processors',
            },
            bases=('shoop.paymentprocessor',),
        ),
        migrations.AddField(
            model_name='waivingcostbehaviorcomponenttranslation',
            name='master',
            field=models.ForeignKey(related_name='translations', editable=False, to='shoop.WaivingCostBehaviorComponent', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='serviceprovidertranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AddField(
            model_name='fixedcostbehaviorcomponenttranslation',
            name='master',
            field=models.ForeignKey(related_name='translations', editable=False, to='shoop.FixedCostBehaviorComponent', null=True),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='payment_processor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='payment processor', blank=True, to='shoop.PaymentProcessor', null=True),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='carrier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='carrier', blank=True, to='shoop.Carrier', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='waivingcostbehaviorcomponenttranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='fixedcostbehaviorcomponenttranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.RunPython(create_default_service_providers, migrations.RunPython.noop),
        migrations.RunPython(set_shop_for_methods, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='paymentmethod',
            name='shop',
            field=models.ForeignKey(to='shoop.Shop', blank=False, null=False, verbose_name='shop'),
        ),
        migrations.AlterField(
            model_name='shippingmethod',
            name='shop',
            field=models.ForeignKey(to='shoop.Shop', blank=False, null=False, verbose_name='shop'),
        ),
    ]
