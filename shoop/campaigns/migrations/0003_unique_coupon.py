# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def make_sure_campaign_coupon_is_unique(apps, schema_editor):
    basket_campaign_model = apps.get_model("campaigns", "BasketCampaign")
    found_coupons = []
    for basket_campaign in basket_campaign_model.objects.all():
        if basket_campaign.coupon and basket_campaign.coupon in found_coupons:
            basket_campaign.coupon = None
            basket_campaign.save()
        elif basket_campaign.coupon:
            found_coupons.append(basket_campaign.coupon)


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0002_update_product_count'),
    ]

    operations = [
        migrations.RunPython(make_sure_campaign_coupon_is_unique, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='basketcampaign',
            name='coupon',
            field=models.OneToOneField(related_name='campaign', null=True, blank=True, to='campaigns.Coupon'),
        ),
    ]
