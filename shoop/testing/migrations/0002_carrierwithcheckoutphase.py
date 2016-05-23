# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0023_add_shipment_identifier'),
        ('shoop_testing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarrierWithCheckoutPhase',
            fields=[
                ('customcarrier_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.CustomCarrier')),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.customcarrier',),
        ),
    ]
