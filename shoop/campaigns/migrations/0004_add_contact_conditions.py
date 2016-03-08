# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0016_shop_contact_address'),
        ('campaigns', '0003_unique_coupon'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='campaigns.BasketCondition')),
                ('contacts', models.ManyToManyField(to='shoop.Contact', verbose_name='contacts')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
        migrations.CreateModel(
            name='ContactCondition',
            fields=[
                ('contextcondition_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='campaigns.ContextCondition')),
                ('contacts', models.ManyToManyField(to='shoop.Contact', verbose_name='contacts')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.contextcondition',),
        ),
        migrations.CreateModel(
            name='ContactGroupBasketCondition',
            fields=[
                ('basketcondition_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='campaigns.BasketCondition')),
                ('contact_groups', models.ManyToManyField(to='shoop.ContactGroup', verbose_name='contact groups')),
            ],
            options={
                'abstract': False,
            },
            bases=('campaigns.basketcondition',),
        ),
    ]
