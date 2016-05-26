# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0024_add_order_modified_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='_codes',
            field=jsonfield.fields.JSONField(blank=True, verbose_name='codes', null=True),
        ),
    ]
