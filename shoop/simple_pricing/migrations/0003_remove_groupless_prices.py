# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db.models import Q


def remove_groupless_prices(apps, schema_editor):
    model = apps.get_model("simple_pricing", "SimpleProductPrice")
    objs = model.objects.filter(Q(group_id__isnull=True) | Q(shop_id__isnull=True))
    if objs.count():
        print("** Removing %d groupless or shopless SimpleProductPrices **" % objs.count())
        objs.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('simple_pricing', '0002_remove_simpleproductprice_includes_tax'),
    ]

    operations = [
        migrations.RunPython(remove_groupless_prices, migrations.RunPython.noop),

        migrations.AlterField(
            model_name='simpleproductprice',
            name='group',
            field=models.ForeignKey(to='shoop.ContactGroup'),
        ),
        migrations.AlterField(
            model_name='simpleproductprice',
            name='shop',
            field=models.ForeignKey(to='shoop.Shop'),
        ),
    ]
