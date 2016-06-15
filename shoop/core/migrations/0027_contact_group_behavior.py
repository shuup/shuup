# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0026_add_account_manager'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupAvailabilityBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, to='shoop.ServiceBehaviorComponent', primary_key=True, serialize=False, auto_created=True)),
                ('groups', models.ManyToManyField(to='shoop.ContactGroup', verbose_name='groups')),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.servicebehaviorcomponent',),
        ),
    ]
