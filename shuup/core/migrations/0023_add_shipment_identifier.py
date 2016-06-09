# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0022_change_order_method_name_lengths'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipment',
            name='identifier',
            field=shuup.core.fields.InternalIdentifierField(null=True, editable=False, max_length=64, blank=True, unique=True),
        ),
    ]
