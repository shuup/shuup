# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0016_shop_contact_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactgroup',
            name='hide_prices',
            field=models.NullBooleanField(default=None, verbose_name='hide prices'),
        ),
        migrations.AddField(
            model_name='contactgroup',
            name='show_prices_including_taxes',
            field=models.NullBooleanField(default=None, verbose_name='show prices including taxes'),
        ),
    ]
