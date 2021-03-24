# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, migrations, models


def combine_refund_types(apps, schema_editor):
    # convert AMOUNT_REFUND (8) to REFUND (6)
    with connection.cursor() as c:
        c.execute("UPDATE shuup_orderline SET type = 6 WHERE type = 8")


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0003_shopproduct_backorder_maximum'),
    ]

    operations = [
        migrations.RunPython(combine_refund_types),
    ]
