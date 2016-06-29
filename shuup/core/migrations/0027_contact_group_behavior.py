# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0026_add_account_manager'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupAvailabilityBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, to='shuup.ServiceBehaviorComponent', primary_key=True, serialize=False, auto_created=True)),
                ('groups', models.ManyToManyField(to='shuup.ContactGroup', verbose_name='groups')),
            ],
            options={
                'abstract': False,
            },
            bases=('shuup.servicebehaviorcomponent',),
        ),
    ]
