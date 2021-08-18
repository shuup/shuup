from django.conf import settings
from django.db import migrations

from shuup import configuration
from shuup.front.setting_keys import SHUUP_FRONT_MAX_UPLOAD_SIZE


def move_settings_to_db(apps, schema_editor):

    configuration.set(None, SHUUP_FRONT_MAX_UPLOAD_SIZE, getattr(settings, "SHUUP_FRONT_MAX_UPLOAD_SIZE", 500000))


class Migration(migrations.Migration):

    dependencies = [
        ("shuup", "0099_move_settings_to_db"),
        ("shuup_front", "0003_add_supplier_and_basket_class_spec_to_stored_basket"),
    ]

    operations = [migrations.RunPython(move_settings_to_db, migrations.RunPython.noop)]
