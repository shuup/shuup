# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop_notify', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='identifier',
            field=shoop.core.fields.InternalIdentifierField(unique=False, editable=False, max_length=64, blank=True, null=True),
        ),
    ]
