# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('simple_supplier', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockadjustment',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
