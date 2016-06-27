# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from decimal import Decimal
import shoop.core.models
import enumfields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0027_contact_group_behavior'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoundingBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.ServiceBehaviorComponent')),
                ('quant', models.DecimalField(default=Decimal('0.05'), verbose_name='rounding quant', max_digits=36, decimal_places=9)),
                ('mode', enumfields.fields.EnumField(default='ROUND_HALF_UP', max_length=10, verbose_name='rounding mode', enum=shoop.core.models.RoundingMode)),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.servicebehaviorcomponent',),
        ),
    ]
