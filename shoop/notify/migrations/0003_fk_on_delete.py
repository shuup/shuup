# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shoop_notify', '0002_notification_identifier'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='marked_read_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='+', editable=False, null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='notification',
            name='recipient',
            field=models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
    ]
