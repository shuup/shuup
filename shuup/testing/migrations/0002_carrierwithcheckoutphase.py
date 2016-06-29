# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0023_add_shipment_identifier'),
        ('shuup_testing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarrierWithCheckoutPhase',
            fields=[
                ('customcarrier_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.CustomCarrier')),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.customcarrier',),
        ),
    ]
