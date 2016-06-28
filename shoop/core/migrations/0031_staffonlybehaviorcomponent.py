# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0030_purchaseorder'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaffOnlyBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoop.ServiceBehaviorComponent')),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.servicebehaviorcomponent',),
        ),
    ]
