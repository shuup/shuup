# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shuup_notify', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='identifier',
            field=shuup.core.fields.InternalIdentifierField(unique=False, editable=False, max_length=64, blank=True, null=True),
        ),
    ]
