# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarrierWithCheckoutPhase',
            fields=[
                ('customcarrier_ptr', models.OneToOneField(to='shuup.CustomCarrier', on_delete=models.CASCADE, parent_link=True, serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.customcarrier',),
        ),
        migrations.CreateModel(
            name='ExpensiveSwedenBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(to='shuup.ServiceBehaviorComponent', on_delete=models.CASCADE, parent_link=True, serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),
        ),
        migrations.CreateModel(
            name='PaymentWithCheckoutPhase',
            fields=[
                ('custompaymentprocessor_ptr', models.OneToOneField(to='shuup.CustomPaymentProcessor', on_delete=models.CASCADE, parent_link=True, serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.custompaymentprocessor',),
        ),
        migrations.CreateModel(
            name='PseudoPaymentProcessor',
            fields=[
                ('paymentprocessor_ptr', models.OneToOneField(to='shuup.PaymentProcessor', on_delete=models.CASCADE, parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('bg_color', models.CharField(verbose_name='Payment Page Background Color', max_length=20, blank=True, default='white')),
                ('fg_color', models.CharField(verbose_name='Payment Page Text Color', max_length=20, blank=True, default='black')),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.paymentprocessor',),
        ),
    ]
