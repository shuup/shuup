from django.conf import settings
from django.db import migrations

from shuup import configuration
from shuup.setting_keys import SHUUP_HOME_CURRENCY


def move_settings_to_db(apps, schema_editor):
    configuration.set(None, SHUUP_HOME_CURRENCY, settings.SHUUP_HOME_CURRENCY)


class Migration(migrations.Migration):

    dependencies = [
        ("shuup", "0098_change_productmedia_verbose_text"),
    ]

    operations = [migrations.RunPython(move_settings_to_db, migrations.RunPython.noop)]
