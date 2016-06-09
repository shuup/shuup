# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0020_services_and_methods'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpensiveSwedenBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.ServiceBehaviorComponent')),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),
        ),
        migrations.CreateModel(
            name='PaymentWithCheckoutPhase',
            fields=[
                ('custompaymentprocessor_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.CustomPaymentProcessor')),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.custompaymentprocessor',),
        ),
        migrations.CreateModel(
            name='PseudoPaymentProcessor',
            fields=[
                ('paymentprocessor_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shuup.PaymentProcessor')),
                ('bg_color', models.CharField(default='white', max_length=20, verbose_name='Payment Page Background Color', blank=True)),
                ('fg_color', models.CharField(default='black', max_length=20, verbose_name='Payment Page Text Color', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.paymentprocessor',),
        ),
    ]
