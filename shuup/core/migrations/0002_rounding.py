# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import enumfields.fields
from decimal import Decimal
from django.db import migrations, models

import shuup.core.models._service_payment


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='custompaymentprocessor',
            name='rounding_mode',
            field=enumfields.fields.EnumField(enum=shuup.core.models._service_payment.RoundingMode, help_text='Rounding mode for cash payment.', max_length=50, verbose_name='rounding mode', default='ROUND_HALF_UP'),
        ),
        migrations.AddField(
            model_name='custompaymentprocessor',
            name='rounding_quantize',
            field=models.DecimalField(max_digits=36, decimal_places=9, verbose_name='rounding quantize', help_text='Rounding quantize for cash payment.', default=Decimal('0.05')),
        ),
        migrations.RemoveField(
            model_name='roundingbehaviorcomponent',
            name='servicebehaviorcomponent_ptr',
        ),
        migrations.DeleteModel(
            name='RoundingBehaviorComponent',
        ),
    ]
