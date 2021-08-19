from django.conf import settings
from django.db import migrations

from shuup import configuration
from shuup.admin.setting_keys import (
    SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION,
    SHUUP_ADMIN_ALLOW_HTML_IN_SUPPLIER_DESCRIPTION,
)


def move_settings_to_db(apps, schema_editor):

    configuration.set(
        None,
        SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION,
        getattr(settings, "SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION", True),
    )
    configuration.set(
        None,
        SHUUP_ADMIN_ALLOW_HTML_IN_SUPPLIER_DESCRIPTION,
        getattr(settings, "SHUUP_ADMIN_ALLOW_HTML_IN_VENDOR_DESCRIPTION", True),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("shuup", "0099_move_settings_to_db"),
        ("shuup_admin", "0001_initial"),
    ]

    operations = [migrations.RunPython(move_settings_to_db, migrations.RunPython.noop)]
