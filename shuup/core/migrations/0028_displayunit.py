# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0027_modify_shop_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='salesunittranslation',
            old_name='short_name',
            new_name='symbol',
        ),
    ]
