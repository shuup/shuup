# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shoop.core.fields


def forwards_func(apps, schema_editor):
    CatalogCampaign = apps.get_model("campaigns", "CatalogCampaign")
    ProductDiscountEffect = apps.get_model("campaigns", "ProductDiscountEffect")
    ProductDiscountAmount = apps.get_model("campaigns", "ProductDiscountAmount")
    ProductDiscountPercentage = apps.get_model("campaigns", "ProductDiscountPercentage")

    BasketCampaign = apps.get_model("campaigns", "BasketCampaign")
    BasketDiscountEffect = apps.get_model("campaigns", "BasketDiscountEffect")
    BasketDiscountAmount = apps.get_model("campaigns", "BasketDiscountAmount")
    BasketDiscountPercentage = apps.get_model("campaigns", "BasketDiscountPercentage")

    ContentType = apps.get_model('contenttypes', 'ContentType')

    db_alias = schema_editor.connection.alias

    def handle(db_alias, obj_cls, base_cls, amount_cls, percentage_cls):
        for c in obj_cls.objects.using(db_alias).all():
            if not c.discount_amount_value and not c.discount_percentage:
                return

            if c.discount_amount_value:
                new_ct = ContentType.objects.get_for_model(amount_cls)
                e = amount_cls()
                e.discount_amount = c.discount_amount_value
            else:
                new_ct = ContentType.objects.get_for_model(percentage_cls)
                e = percentage_cls()
                e.discount_percentage = c.discount_percentage
            e.campaign = c
            e.save()

            base_cls.objects.filter(polymorphic_ctype__isnull=True, campaign_id=c.id).update(polymorphic_ctype=new_ct)

    handle(db_alias,
           obj_cls=BasketCampaign,
           base_cls=BasketDiscountEffect,
           amount_cls=BasketDiscountAmount,
           percentage_cls=BasketDiscountPercentage)

    handle(db_alias,
           obj_cls=CatalogCampaign,
           base_cls=ProductDiscountEffect,
           amount_cls=ProductDiscountAmount,
           percentage_cls=ProductDiscountPercentage)


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('campaigns', '0005_sales_ranges'),
    ]

    operations = [
        migrations.CreateModel(
            name='BasketDiscountEffect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductDiscountEffect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BasketDiscountAmount',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='campaigns.BasketDiscountEffect', parent_link=True, serialize=False)),
                ('discount_amount', shoop.core.fields.MoneyValueField(max_digits=36, blank=True, null=True, default=None, help_text='Flat amount of discount.', verbose_name='discount amount', decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect',),
        ),
        migrations.CreateModel(
            name='BasketDiscountPercentage',
            fields=[
                ('basketdiscounteffect_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='campaigns.BasketDiscountEffect', parent_link=True, serialize=False)),
                ('discount_percentage', models.DecimalField(max_digits=6, blank=True, null=True, help_text='The discount percentage for this campaign.', verbose_name='discount percentage', decimal_places=5)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketdiscounteffect',),
        ),
        migrations.CreateModel(
            name='ProductDiscountAmount',
            fields=[
                ('productdiscounteffect_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='campaigns.ProductDiscountEffect', parent_link=True, serialize=False)),
                ('discount_amount', shoop.core.fields.MoneyValueField(max_digits=36, blank=True, null=True, default=None, help_text='Flat amount of discount.', verbose_name='discount amount', decimal_places=9)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.productdiscounteffect',),
        ),
        migrations.CreateModel(
            name='ProductDiscountPercentage',
            fields=[
                ('productdiscounteffect_ptr', models.OneToOneField(auto_created=True, primary_key=True, to='campaigns.ProductDiscountEffect', parent_link=True, serialize=False)),
                ('discount_percentage', models.DecimalField(max_digits=6, blank=True, null=True, help_text='The discount percentage for this campaign.', verbose_name='discount percentage', decimal_places=5)),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.productdiscounteffect',),
        ),
        migrations.AddField(
            model_name='productdiscounteffect',
            name='campaign',
            field=models.ForeignKey(related_name='effects', to='campaigns.CatalogCampaign', verbose_name='campaign'),
        ),
        migrations.AddField(
            model_name='productdiscounteffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_campaigns.productdiscounteffect_set+', editable=False, null=True, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='basketdiscounteffect',
            name='campaign',
            field=models.ForeignKey(related_name='effects', to='campaigns.BasketCampaign', verbose_name='campaign'),
        ),
        migrations.AddField(
            model_name='basketdiscounteffect',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_campaigns.basketdiscounteffect_set+', editable=False, null=True, to='contenttypes.ContentType'),
        ),
        migrations.RunPython(forwards_func),
        migrations.RemoveField(
            model_name='basketcampaign',
            name='discount_amount_value',
        ),
        migrations.RemoveField(
            model_name='basketcampaign',
            name='discount_percentage',
        ),
        migrations.RemoveField(
            model_name='catalogcampaign',
            name='discount_amount_value',
        ),
        migrations.RemoveField(
            model_name='catalogcampaign',
            name='discount_percentage',
        ),

    ]
