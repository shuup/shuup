# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0017_contact_group_price_display_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='personcontact',
            name='first_name',
            field=models.CharField(max_length=30, verbose_name='first name', blank=True),
        ),
        migrations.AddField(
            model_name='personcontact',
            name='last_name',
            field=models.CharField(max_length=50, verbose_name='last name', blank=True),
        ),
    ]
