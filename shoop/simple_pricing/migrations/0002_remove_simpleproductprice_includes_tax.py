# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simple_pricing', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='simpleproductprice',
            name='includes_tax',
        ),
    ]
