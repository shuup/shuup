# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields

def add_identifiers(apps, schema_editor):
    for model_name in ("Attribute", "OrderStatus"):
        model = apps.get_model("shoop", model_name)
        for obj in model.objects.filter(identifier__isnull=True):
            obj.identifier = "%s%s" % (model_name, obj.pk)
            obj.save(update_fields=("identifier",))


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_identifiers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='attribute',
            name='identifier',
            field=shoop.core.fields.InternalIdentifierField(unique=True, blank=False, max_length=64, null=False, editable=False),
        ),
        migrations.AlterField(
            model_name='orderstatus',
            name='identifier',
            field=shoop.core.fields.InternalIdentifierField(unique=True, blank=False, db_index=True, max_length=64, null=False, editable=False),
        ),
        migrations.AlterField(
            model_name='productvariationvariable',
            name='identifier',
            field=shoop.core.fields.InternalIdentifierField(blank=True, unique=False, max_length=64, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='productvariationvariablevalue',
            name='identifier',
            field=shoop.core.fields.InternalIdentifierField(blank=True, unique=False, max_length=64, null=True, editable=False),
        ),
    ]
