# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0022_change_order_method_name_lengths'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipment',
            name='identifier',
            field=shoop.core.fields.InternalIdentifierField(null=True, editable=False, max_length=64, blank=True, unique=True),
        ),
    ]
