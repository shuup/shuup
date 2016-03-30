# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0018_add_first_and_last_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='merchant_notes',
            field=models.TextField(verbose_name='merchant notes', blank=True),
        ),
    ]
