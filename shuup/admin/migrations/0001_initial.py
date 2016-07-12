# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def _get_content_type(apps, model_name):
    ContentType = apps.get_model("contenttypes", "ContentType")
    return ContentType.objects.get_for_model(apps.get_model("shuup", model_name))


def create_dashboard_permissions(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    order_content_type = _get_content_type(apps, "Order")
    Permission.objects.create(
        codename="view_sales_dashboard",
        name="Can view sales dashboard",
        content_type=order_content_type,
    )

    contact_content_type = _get_content_type(apps, "Contact")
    Permission.objects.create(
        codename="view_customers_dashboard",
        name="Can view customers dashboard",
        content_type=contact_content_type,
    )


def delete_dashboard_permissions(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")

    order_content_type = _get_content_type(apps, "Order")
    Permission.objects.filter(
        codename="view_sales_dashboard",
        content_type=order_content_type,
    ).delete()

    contact_content_type = _get_content_type(apps, "Contact")
    Permission.objects.filter(
        codename="view_customers_dashboard",
        content_type=contact_content_type,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.RunPython(create_dashboard_permissions, delete_dashboard_permissions),
    ]
