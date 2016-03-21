# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt
import mptt.fields
import mptt.managers


def rebuild_pages(apps, schema_editor):
    manager = mptt.managers.TreeManager()
    page_model = apps.get_model("shoop_simple_cms", "Page")
    manager.model = page_model
    mptt.register(page_model, order_insertion_by=["-available_from"])
    manager.contribute_to_class(page_model, 'objects')
    manager.rebuild()


class Migration(migrations.Migration):

    dependencies = [
        ('shoop_simple_cms', '0003_verbose_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='level',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='page',
            name='lft',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='page',
            name='list_children_on_page',
            field=models.BooleanField(default=False, verbose_name='list children on page'),
        ),
        migrations.AddField(
            model_name='page',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='children', verbose_name='parent', blank=True, to='shoop_simple_cms.Page', null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='rght',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='page',
            name='tree_id',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.RunPython(rebuild_pages, migrations.RunPython.noop)
    ]
