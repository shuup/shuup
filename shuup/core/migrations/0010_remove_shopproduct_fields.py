# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import apps
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0009_update_tax_name_max_length'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shopproduct',
            name='visible',
        ),
        migrations.RemoveField(
            model_name='shopproduct',
            name='listed',
        ),
        migrations.RemoveField(
            model_name='shopproduct',
            name='searchable',
        ),

    ]

    def _can_run(self):
        ShopProduct = apps.get_model("shuup", "ShopProduct")
        fields = set([field.name for field in ShopProduct._meta.local_fields])
        needles = ["visible", "listed", "searchable"]
        return fields.issuperset(set(needles))

    def apply(self, project_state, schema_editor, collect_sql=False):
        if self._can_run():  # only run migrations if `ShopProduct` have the actual fields
            return super(Migration, self).apply(project_state, schema_editor, collect_sql)

    def unapply(self, project_state, schema_editor, collect_sql=False):
        if self._can_run():  # only run migrations if `ShopProduct` have the actual fields
            return super(Migration, self).unapply(project_state, schema_editor, collect_sql)
