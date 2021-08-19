from django.conf import settings
from django.db import migrations

from shuup import configuration
from shuup.reports.constants import DEFAULT_REPORTS_ITEM_LIMIT
from shuup.reports.setting_keys import SHUUP_DEFAULT_REPORTS_ITEM_LIMIT


def move_settings_to_db(apps, schema_editor):
    print("reports move_settings_to_db")
    configuration.set(
        None,
        SHUUP_DEFAULT_REPORTS_ITEM_LIMIT,
        getattr(settings, "DEFAULT_REPORTS_ITEM_LIMIT", DEFAULT_REPORTS_ITEM_LIMIT),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("shuup", "0099_move_settings_to_db"),
    ]

    operations = [migrations.RunPython(move_settings_to_db, migrations.RunPython.noop)]
