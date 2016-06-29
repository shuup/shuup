# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from decimal import Decimal
import shuup.core.models
import enumfields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0027_contact_group_behavior'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoundingBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.ServiceBehaviorComponent')),
                ('quant', models.DecimalField(default=Decimal('0.05'), verbose_name='rounding quant', max_digits=36, decimal_places=9)),
                ('mode', enumfields.fields.EnumField(default='ROUND_HALF_UP', max_length=50, verbose_name='rounding mode', enum=shuup.core.models.RoundingMode)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),
        ),
    ]
