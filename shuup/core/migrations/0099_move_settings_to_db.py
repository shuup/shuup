from django.conf import settings
from django.db import migrations

from shuup import configuration
from shuup.core.setting_keys import SHUUP_ADDRESS_HOME_COUNTRY, SHUUP_ALLOW_ANONYMOUS_ORDERS, SHUUP_HOME_CURRENCY


def move_settings_to_db(apps, schema_editor):
    configuration.set(None, SHUUP_HOME_CURRENCY, settings.SHUUP_HOME_CURRENCY)
    configuration.set(None, SHUUP_ADDRESS_HOME_COUNTRY, settings.SHUUP_ADDRESS_HOME_COUNTRY)
    configuration.set(None, SHUUP_ALLOW_ANONYMOUS_ORDERS, settings.SHUUP_ALLOW_ANONYMOUS_ORDERS)


class Migration(migrations.Migration):

    dependencies = [
        ("shuup", "0098_change_productmedia_verbose_text"),
    ]

    operations = [migrations.RunPython(move_settings_to_db, migrations.RunPython.noop)]
