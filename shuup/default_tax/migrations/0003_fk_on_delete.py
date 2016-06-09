# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('default_tax', '0002_tax_price_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxrule',
            name='tax',
            field=models.ForeignKey(to='shuup.Tax', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
