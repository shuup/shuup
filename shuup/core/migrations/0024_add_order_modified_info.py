# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shuup.core.fields
import django.db.models.deletion
from django.conf import settings


def init_modified_info(apps, schema_editor):
    order_model = apps.get_model("shuup", "Order")
    order_model.objects.update(
        modified_on=models.F("created_on"),
        modified_by=models.F("creator")
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shuup', '0023_add_shipment_identifier'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='modified_by',
            field=shuup.core.fields.UnsavedForeignKey(
                null=True, verbose_name='modifier user', blank=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='orders_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='order',
            name='modified_on',
            field=models.DateTimeField(null=True, verbose_name='modified on', auto_now_add=True),
        ),
        migrations.RunPython(init_modified_info, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='modified_on',
            field=models.DateTimeField(verbose_name='modified on', auto_now_add=True),
        ),
    ]
